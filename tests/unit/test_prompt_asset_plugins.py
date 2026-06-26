import base64

import pytest

from airedteam.builtins.executors.crescendo import CrescendoExecutor
from airedteam.builtins.executors.pair import PAIRExecutor
from airedteam.builtins.scorers.llm_judge import LLMJudgeScorer
from airedteam.core.types import AttemptResult, Prompt, Response
from airedteam.services.prompt_assets import PromptAssetService
from airedteam.storage import models
from airedteam.storage.blobs import LocalBlobStore
from airedteam.storage.db import make_engine, make_sessionmaker


class FakeTarget:
    name = "fake"

    def __init__(self, replies):
        self.replies = list(replies)
        self.seen: list[str] = []

    async def generate(self, prompt):
        self.seen.append(prompt.text)
        return Response(text=self.replies.pop(0), raw={}, latency_ms=1)

    async def chat(self, messages):
        return Response(text="target response", raw={}, latency_ms=1)

    async def aclose(self):
        return None


class FailingOnceTarget(FakeTarget):
    async def generate(self, prompt):
        self.seen.append(prompt.text)
        if len(self.seen) == 1:
            raise RuntimeError("HTTPStatusError: blocked")
        return Response(text=self.replies.pop(0), raw={}, latency_ms=1)


def _decode_base64_retry_prompt(prompt_text: str) -> str:
    encoded = prompt_text.split("<evaluation_prompt_base64>\n", 1)[1].split(
        "\n</evaluation_prompt_base64>",
        1,
    )[0]
    return base64.b64decode(encoded.encode("ascii")).decode("utf-8")


@pytest.mark.asyncio
async def test_llm_judge_uses_prompt_asset_and_returns_snapshot(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    assets = PromptAssetService(sessions, LocalBlobStore(tmp_path / "blobs"))
    override = await assets.create_override(
        "llm_judge.single.v2",
        name="short",
        template="JUDGE {original_prompt} / {prompt} / {response} / {rubric}",
    )

    judge = FakeTarget(['{"label": true, "confidence": 0.9, "rationale": "ok"}'])
    scorer = LLMJudgeScorer(judge=judge, rubric="R", prompt_assets=assets, prompt_override_id=override["id"])
    score = await scorer.score(
        AttemptResult(
            prompt=Prompt(text="P", metadata={"original_prompt_text": "O"}),
            response=Response(text="A", raw={}, latency_ms=1),
        )
    )

    assert judge.seen == ["JUDGE O / P / A / R"]
    assert score.prompt_snapshot["asset_id"] == "llm_judge.single.v2"
    assert score.prompt_snapshot["override_id"] == override["id"]
    assert score.prompt_snapshot["rendered_text"] == "JUDGE O / P / A / R"


@pytest.mark.asyncio
async def test_llm_judge_prompt_snapshot_records_base64_retry(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    assets = PromptAssetService(sessions, LocalBlobStore(tmp_path / "blobs"))

    judge = FailingOnceTarget(['{"label": false, "confidence": 0.9, "rationale": "safe"}'])
    scorer = LLMJudgeScorer(judge=judge, rubric="R", prompt_assets=assets)
    score = await scorer.score(
        AttemptResult(
            prompt=Prompt(text="P", metadata={"original_prompt_text": "O"}),
            response=Response(text="A", raw={}, latency_ms=1),
        )
    )

    assert score.value["judge_retry_used"] is True
    assert score.value["judge_retry_strategy"] == "base64_evaluation_prompt"
    assert score.prompt_snapshot["asset_id"] == "llm_judge.single.v2"
    assert score.prompt_snapshot["retry"]["used"] is True
    assert score.prompt_snapshot["retry"]["strategy"] == "base64_evaluation_prompt"
    assert "<evaluation_prompt_base64>" in score.prompt_snapshot["rendered_text"]
    decoded = _decode_base64_retry_prompt(score.prompt_snapshot["rendered_text"])
    assert "<original_prompt>\nO\n</original_prompt>" in decoded
    assert "<prompt>\nP\n</prompt>" in decoded
    assert "<response>\nA\n</response>" in decoded
    assert len(judge.seen) == 2


@pytest.mark.asyncio
async def test_crescendo_uses_prompt_asset_and_returns_snapshots(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    assets = PromptAssetService(sessions, LocalBlobStore(tmp_path / "blobs"))
    override = await assets.create_override(
        "crescendo.attacker.v1",
        name="short",
        template="NEXT {goal} AFTER {transcript}",
    )

    attacker = FakeTarget(["followup"])
    executor = CrescendoExecutor(
        attacker=attacker, goal="G", max_turns=2, prompt_assets=assets, attacker_prompt_override_id=override["id"]
    )
    result = await executor.run(Prompt(text="seed"), FakeTarget([]), [])

    assert attacker.seen == ["NEXT G AFTER USER: seed\nASSISTANT: target response"]
    assert result.prompt_snapshots
    assert result.prompt_snapshots[0]["asset_id"] == "crescendo.attacker.v1"
    assert result.prompt_snapshots[0]["override_id"] == override["id"]


@pytest.mark.asyncio
async def test_pair_uses_prompt_assets_and_returns_snapshots(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    assets = PromptAssetService(sessions, LocalBlobStore(tmp_path / "blobs"))

    attacker = FakeTarget(['{"prompt": "try-2", "improvement": "x"}'])
    judge = FakeTarget(['{"score": 9, "rationale": "done"}'])
    executor = PAIRExecutor(attacker=attacker, judge=judge, goal="G", max_turns=2, prompt_assets=assets)
    result = await executor.run(Prompt(text="try-1"), FakeTarget([]), [])

    asset_ids = [s["asset_id"] for s in result.prompt_snapshots]
    assert asset_ids == ["pair.judge.v1"]
    assert "GOAL:\nG" in judge.seen[0]
