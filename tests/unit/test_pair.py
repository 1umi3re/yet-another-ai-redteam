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


@pytest.mark.asyncio
async def test_pair_resets_judge_state_between_runs():
    """Ensure judge state doesn't leak between successive runs of the same executor."""
    # First run: judge returns score 10 on both turns
    atk = Scripted("a", ['{"prompt": "p1-a", "improvement": "x"}',
                         '{"prompt": "p2-a", "improvement": "x"}'])
    tgt = Scripted("t", ["r1", "r2"])
    jdg = Scripted("j", ['{"score": 10, "rationale": "win-1"}',
                         '{"score": 10, "rationale": "win-2"}'])
    ex = PAIRExecutor(attacker=atk, judge=jdg, max_turns=5, goal="g")
    await ex.run(Prompt(text="seed-1"), tgt, [])
    
    # First run ends with judge score 10 set in self._last_score.
    # After first run, reuse executor for second run.
    # Clear attacker history and set up for second run.
    atk.seen.clear()
    atk.replies = ['{"prompt": "p2-turn2", "improvement": "x"}']
    tgt.replies = ["r2a"]
    # Second run: judge returns score 1 (very different from 10)
    jdg.replies = ['{"score": 1, "rationale": "refused"}']
    await ex.run(Prompt(text="seed-2"), tgt, [])
    
    # First attacker call in second run happens at turn 1, after turn 0's judge call.
    # It should show the NEW judge score (1) from turn 0 of run 2, not the old score (10).
    # If the bug existed, it would show 10.
    assert "JUDGE SCORE: 1" in atk.seen[0]
    assert "JUDGE SCORE: 10" not in atk.seen[0]
