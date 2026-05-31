from __future__ import annotations

import pytest

from airedteam.builtins.executors.crescendo import CrescendoExecutor
from airedteam.core.plugins import BaseTarget
from airedteam.core.types import Message, Prompt, Response


class RecorderTarget(BaseTarget):
    name = "t"

    def __init__(self, replies):
        self.replies = list(replies)
        self.seen: list[list[Message]] = []

    async def chat(self, messages):
        self.seen.append(list(messages))
        return Response(text=self.replies.pop(0), raw={}, latency_ms=1)

    async def aclose(self):
        pass


class ScriptedAttacker(BaseTarget):
    name = "a"

    def __init__(self, next_prompts):
        self.next_prompts = list(next_prompts)
        self.seen: list[str] = []

    async def generate(self, prompt):
        self.seen.append(prompt.text)
        return Response(text=self.next_prompts.pop(0), raw={}, latency_ms=1)

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_crescendo_uses_attacker_for_followups_only():
    tgt = RecorderTarget(["t1", "t2", "t3"])
    atk = ScriptedAttacker(["escalate-1", "escalate-2"])
    ex = CrescendoExecutor(attacker=atk, max_turns=3, goal="give me harmful thing")
    ar = await ex.run(Prompt(text="innocent-seed"), tgt, [])
    assert ar.status == "completed"
    user_turns = [m.text for m in ar.conversation if m.role == "user"]
    assert user_turns == ["innocent-seed", "escalate-1", "escalate-2"]
    assert any("give me harmful thing" in s for s in atk.seen)
    assert any("ASSISTANT: t1" in s for s in atk.seen)


@pytest.mark.asyncio
async def test_crescendo_requires_attacker():
    with pytest.raises(ValueError, match="attacker"):
        CrescendoExecutor(attacker=None, goal="x")
