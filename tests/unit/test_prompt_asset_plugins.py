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


@pytest.mark.asyncio
async def test_llm_judge_uses_prompt_asset_and_returns_snapshot(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    assets = PromptAssetService(sessions, LocalBlobStore(tmp_path / "blobs"))
    override = await assets.create_override(
        "llm_judge.single.v1",
        name="short",
        template="JUDGE {prompt} / {response} / {rubric}",
    )

    judge = FakeTarget(['{"label": true, "confidence": 0.9, "rationale": "ok"}'])
    scorer = LLMJudgeScorer(judge=judge, rubric="R", prompt_assets=assets, prompt_override_id=override["id"])
    score = await scorer.score(
        AttemptResult(
            prompt=Prompt(text="P"),
            response=Response(text="A", raw={}, latency_ms=1),
        )
    )

    assert judge.seen == ["JUDGE P / A / R"]
    assert score.prompt_snapshot["asset_id"] == "llm_judge.single.v1"
    assert score.prompt_snapshot["override_id"] == override["id"]
    assert score.prompt_snapshot["rendered_text"] == "JUDGE P / A / R"


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
