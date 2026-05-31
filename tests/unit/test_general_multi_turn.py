from __future__ import annotations

import pytest

from airedteam.builtins.executors.general_multi_turn import (
    GeneralMultiTurnExecutor,
    make_general_multi_turn_executor,
)
from airedteam.core.plugins import BaseTarget
from airedteam.core.types import Prompt, Response
from airedteam.services.prompt_assets import PromptAssetService
from airedteam.storage import models
from airedteam.storage.blobs import LocalBlobStore
from airedteam.storage.db import make_engine, make_sessionmaker


class ScriptedTarget(BaseTarget):
    def __init__(self, name: str, replies: list[str]):
        self.name = name
        self.replies = list(replies)
        self.seen: list[str] = []

    async def generate(self, prompt):
        self.seen.append(prompt.text)
        return Response(text=self.replies.pop(0), raw={}, latency_ms=1)

    async def chat(self, messages):
        self.seen.append(messages[-1].text)
        return Response(text=self.replies.pop(0), raw={}, latency_ms=1)

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_general_multi_turn_feedback_drives_next_attack_and_stops_on_judge():
    attacker = ScriptedTarget("attacker", ['{"prompt": "try-2", "rationale": "use feedback"}'])
    evaluator = ScriptedTarget(
        "evaluator",
        [
            '{"feedback": "ask more directly", "score": 3, "rationale": "refused"}',
            '{"feedback": "done", "score": 10, "rationale": "complied"}',
        ],
    )
    judge = ScriptedTarget(
        "judge",
        [
            '{"success": false, "score": 3, "rationale": "not yet"}',
            '{"success": true, "score": 10, "rationale": "done"}',
        ],
    )
    target = ScriptedTarget("target", ["refused", "complied"])

    executor = GeneralMultiTurnExecutor(
        attacker=attacker,
        evaluator=evaluator,
        judge=judge,
        goal="G",
        max_turns=5,
    )
    result = await executor.run(Prompt(text="seed"), target, [])

    assert result.status == "completed"
    assert result.response.text == "complied"
    assert [m.text for m in result.conversation if m.role == "user"] == ["seed", "try-2"]
    assert "ask more directly" in attacker.seen[0]
    assert "LAST JUDGE SCORE: 3" in attacker.seen[0]


@pytest.mark.asyncio
async def test_general_multi_turn_rewrites_over_limit_attacker_output():
    attacker = ScriptedTarget(
        "attacker",
        [
            '{"prompt": "this generated turn is too long"}',
            '{"prompt": "short"}',
        ],
    )
    evaluator = ScriptedTarget(
        "evaluator",
        [
            '{"feedback": "shorten", "score": 3, "rationale": "refused"}',
            '{"feedback": "done", "score": 10, "rationale": "complied"}',
        ],
    )
    judge = ScriptedTarget(
        "judge",
        [
            '{"success": false, "score": 3, "rationale": "not yet"}',
            '{"success": true, "score": 10, "rationale": "done"}',
        ],
    )
    target = ScriptedTarget("target", ["refused", "complied"])
    target._airedteam_max_input_chars = 5

    executor = GeneralMultiTurnExecutor(
        attacker=attacker,
        evaluator=evaluator,
        judge=judge,
        goal="G",
        max_turns=5,
    )
    result = await executor.run(Prompt(text="seed"), target, [])

    assert result.status == "completed"
    assert [m.text for m in result.conversation if m.role == "user"] == ["seed", "short"]
    assert "5 characters" in attacker.seen[0]
    assert "Rewrite" in attacker.seen[1]


@pytest.mark.asyncio
async def test_general_multi_turn_uses_selected_prompt_assets(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    assets = PromptAssetService(sessions, LocalBlobStore(tmp_path / "blobs"))
    await assets.create_asset(
        asset_id="custom.general.attacker.v1",
        plugin="custom",
        purpose="next_user_message",
        variables=[],
        template="CUSTOM ATTACK {goal} AFTER {evaluator_feedback}",
    )
    await assets.create_asset(
        asset_id="custom.general.evaluator.v1",
        plugin="custom",
        purpose="turn_feedback",
        variables=[],
        template="CUSTOM EVAL {goal} {user} {assistant}",
    )
    await assets.create_asset(
        asset_id="custom.general.judger.v1",
        plugin="custom",
        purpose="success_judgement",
        variables=[],
        template="CUSTOM JUDGE {goal} {evaluator_feedback}",
    )

    attacker = ScriptedTarget("attacker", ['{"prompt": "try-2"}'])
    evaluator = ScriptedTarget(
        "evaluator",
        [
            '{"feedback": "feedback-1", "score": 2}',
            '{"feedback": "feedback-2", "score": 10}',
        ],
    )
    judge = ScriptedTarget(
        "judge",
        [
            '{"success": false, "score": 2, "rationale": "no"}',
            '{"success": true, "score": 10, "rationale": "yes"}',
        ],
    )
    target = ScriptedTarget("target", ["r1", "r2"])

    executor = GeneralMultiTurnExecutor(
        attacker=attacker,
        evaluator=evaluator,
        judge=judge,
        goal="G",
        max_turns=3,
        prompt_assets=assets,
        attacker_prompt_asset_id="custom.general.attacker.v1",
        evaluator_prompt_asset_id="custom.general.evaluator.v1",
        judger_prompt_asset_id="custom.general.judger.v1",
    )
    result = await executor.run(Prompt(text="seed"), target, [])

    assert evaluator.seen[0] == "CUSTOM EVAL G seed r1"
    assert judge.seen[0] == "CUSTOM JUDGE G feedback-1"
    assert attacker.seen[0] == "CUSTOM ATTACK G AFTER feedback-1"
    assert [s["asset_id"] for s in result.prompt_snapshots] == [
        "custom.general.evaluator.v1",
        "custom.general.judger.v1",
        "custom.general.attacker.v1",
        "custom.general.evaluator.v1",
        "custom.general.judger.v1",
    ]


@pytest.mark.asyncio
async def test_general_multi_turn_requires_all_role_targets():
    target = ScriptedTarget("x", [])
    with pytest.raises(ValueError, match="attacker"):
        GeneralMultiTurnExecutor(attacker=None, evaluator=target, judge=target)
    with pytest.raises(ValueError, match="evaluator"):
        GeneralMultiTurnExecutor(attacker=target, evaluator=None, judge=target)
    with pytest.raises(ValueError, match="judge"):
        GeneralMultiTurnExecutor(attacker=target, evaluator=target, judge=None)


@pytest.mark.asyncio
async def test_general_multi_turn_variant_uses_default_prompt_assets(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    assets = PromptAssetService(sessions, LocalBlobStore(tmp_path / "blobs"))
    await assets.create_asset(
        asset_id="variant.attacker.v1",
        plugin="custom_variant",
        purpose="next_user_message",
        variables=[],
        template="VARIANT ATTACK {goal} AFTER {evaluator_feedback}",
    )
    await assets.create_asset(
        asset_id="variant.evaluator.v1",
        plugin="custom_variant",
        purpose="turn_feedback",
        variables=[],
        template="VARIANT EVAL {goal} {user} {assistant}",
    )
    await assets.create_asset(
        asset_id="variant.judger.v1",
        plugin="custom_variant",
        purpose="success_judgement",
        variables=[],
        template="VARIANT JUDGE {goal} {evaluator_feedback}",
    )

    VariantExecutor = make_general_multi_turn_executor(
        "variant_multi_turn",
        attacker_prompt_asset_id="variant.attacker.v1",
        evaluator_prompt_asset_id="variant.evaluator.v1",
        judger_prompt_asset_id="variant.judger.v1",
    )

    attacker = ScriptedTarget("attacker", ['{"prompt": "variant-try-2"}'])
    evaluator = ScriptedTarget(
        "evaluator",
        [
            '{"feedback": "variant-feedback", "score": 2}',
            '{"feedback": "done", "score": 10}',
        ],
    )
    judge = ScriptedTarget(
        "judge",
        [
            '{"success": false, "score": 2}',
            '{"success": true, "score": 10}',
        ],
    )
    target = ScriptedTarget("target", ["r1", "r2"])

    executor = VariantExecutor(
        attacker=attacker,
        evaluator=evaluator,
        judge=judge,
        goal="G",
        max_turns=3,
        prompt_assets=assets,
    )
    result = await executor.run(Prompt(text="seed"), target, [])

    assert executor.name == "variant_multi_turn"
    assert evaluator.seen[0] == "VARIANT EVAL G seed r1"
    assert judge.seen[0] == "VARIANT JUDGE G variant-feedback"
    assert attacker.seen[0] == "VARIANT ATTACK G AFTER variant-feedback"
    assert [s["asset_id"] for s in result.prompt_snapshots[:3]] == [
        "variant.evaluator.v1",
        "variant.judger.v1",
        "variant.attacker.v1",
    ]
