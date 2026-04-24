from __future__ import annotations
import pytest
from airedteam.core.types import Prompt, Response, Message, AttemptResult
from airedteam.core.plugins import BaseTarget
from airedteam.builtins.executors.multi_turn_base import MultiTurnExecutor


class ScriptedTarget(BaseTarget):
    name = "scripted"
    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.calls: list[list[Message]] = []
    async def chat(self, messages):
        self.calls.append(list(messages))
        return Response(text=self.replies.pop(0), raw={}, latency_ms=1)
    async def aclose(self): pass


class TwoStepExec(MultiTurnExecutor):
    name = "two_step"
    max_turns = 2
    async def next_user_message(self, state, last_response):
        if state["turn"] == 0:
            return Message(role="user", text=state["seed"].text)
        return Message(role="user", text="follow up")
    async def should_stop(self, state, last_response):
        return state["turn"] >= self.max_turns


@pytest.mark.asyncio
async def test_multi_turn_base_runs_two_turns_and_fills_conversation():
    tgt = ScriptedTarget(["r1", "r2"])
    ex = TwoStepExec()
    ar = await ex.run(Prompt(text="seed"), tgt, [])
    assert ar.status == "completed"
    assert ar.response.text == "r2"
    assert [m.role for m in ar.conversation] == ["user", "assistant", "user", "assistant"]
    assert ar.conversation[0].text == "seed"
    assert ar.conversation[-1].text == "r2"


@pytest.mark.asyncio
async def test_multi_turn_base_respects_converters_on_first_turn_only():
    class UpperCase:
        name = "upper"
        async def convert(self, p: Prompt):
            return Prompt(text=p.text.upper(), metadata=p.metadata)
    tgt = ScriptedTarget(["a", "b"])
    ex = TwoStepExec()
    ar = await ex.run(Prompt(text="seed"), tgt, [UpperCase()])
    assert ar.converter_chain == ["upper"]
    assert tgt.calls[0][0].text == "SEED"
    assert tgt.calls[1][-1].text == "follow up"
