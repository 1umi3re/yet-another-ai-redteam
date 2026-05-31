from __future__ import annotations

import pytest

from airedteam.builtins.converters.encoding.base64_conv import Base64Converter
from airedteam.builtins.executors.best_of_n import BestOfNExecutor
from airedteam.core.types import Prompt, Response


class ScriptedTarget:
    name = "scripted"

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.seen: list[str] = []

    async def generate(self, prompt: Prompt) -> Response:
        self.seen.append(prompt.text)
        return Response(text=self.replies.pop(0), raw={}, latency_ms=1)

    async def aclose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_best_of_n_runs_variants_and_selects_non_refusal_response():
    target = ScriptedTarget(
        [
            "I cannot help with that.",
            "Here is the detailed answer with more content.",
            "short answer",
        ]
    )
    executor = BestOfNExecutor(attempts=3, seed=7)

    result = await executor.run(Prompt(text="answer this"), target, [])

    assert result.status == "completed"
    assert result.response.text == "Here is the detailed answer with more content."
    assert len(target.seen) == 3
    assert len(set(target.seen)) == 3
    assert result.prompt.metadata["best_of_n"]["candidate_count"] == 3
    assert result.prompt.metadata["best_of_n"]["selected_index"] == 1
    assert result.prompt.metadata["best_of_n"]["candidates"][0]["response_text"].startswith("I cannot")


@pytest.mark.asyncio
async def test_best_of_n_applies_converters_before_variant_generation():
    target = ScriptedTarget(["ok 1", "ok 2"])
    executor = BestOfNExecutor(attempts=2, seed=1)

    result = await executor.run(Prompt(text="hi"), target, [Base64Converter(wrap=False)])

    assert result.status == "completed"
    assert result.converter_chain == ["base64"]
    assert all(seen != "hi" for seen in target.seen)
    assert "aGk=" in target.seen[0]


@pytest.mark.asyncio
async def test_best_of_n_returns_failed_when_all_candidates_fail():
    class FailingTarget:
        name = "bad"

        async def generate(self, prompt: Prompt):
            raise RuntimeError("boom")

        async def aclose(self) -> None:
            return None

    result = await BestOfNExecutor(attempts=2).run(Prompt(text="x"), FailingTarget(), [])

    assert result.status == "failed"
    assert "all best_of_n candidates failed" in result.error
    assert result.prompt.metadata["best_of_n"]["candidate_count"] == 2
