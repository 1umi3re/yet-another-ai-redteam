from __future__ import annotations
import pytest
from airedteam.core.types import Prompt, Response, Message
from airedteam.core.plugins import BaseTarget
from airedteam.builtins.executors.pair import PAIRExecutor


class Scripted(BaseTarget):
    def __init__(self, name, replies):
        self.name = name; self.replies = list(replies); self.seen = []
    async def generate(self, prompt):
        self.seen.append(prompt.text)
        return Response(text=self.replies.pop(0), raw={}, latency_ms=1)
    async def chat(self, messages):
        self.seen.append(messages[-1].text)
        return Response(text=self.replies.pop(0), raw={}, latency_ms=1)
    async def aclose(self): pass


@pytest.mark.asyncio
async def test_pair_stops_early_when_judge_reports_success():
    atk = Scripted("a", ['{"prompt": "try-1", "improvement": "init"}',
                        '{"prompt": "try-2", "improvement": "more personal"}'])
    tgt = Scripted("t", ["refused", "sure here"])
    jdg = Scripted("j", ['{"score": 3, "rationale": "refused"}',
                         '{"score": 10, "rationale": "complied"}'])
    ex = PAIRExecutor(attacker=atk, judge=jdg, max_turns=5, goal="get harmful")
    ar = await ex.run(Prompt(text="seed"), tgt, [])
    assert ar.status == "completed"
    assert sum(1 for m in ar.conversation if m.role == "assistant") == 2


@pytest.mark.asyncio
async def test_pair_requires_judge_and_attacker():
    with pytest.raises(ValueError, match="attacker"):
        PAIRExecutor(attacker=None, judge=Scripted("j", []), goal="x")
    with pytest.raises(ValueError, match="judge"):
        PAIRExecutor(attacker=Scripted("a", []), judge=None, goal="x")
