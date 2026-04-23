import pytest
from airedteam.builtins.scorers.regex import RegexScorer
from airedteam.core.types import AttemptResult, Prompt, Response


def _ar(t): return AttemptResult(prompt=Prompt(text="x"), response=Response(text=t, raw={}, latency_ms=1))


@pytest.mark.asyncio
async def test_regex_match():
    s = RegexScorer(pattern=r"step\s+\d+:", flags="i")
    assert (await s.score(_ar("Step 1: do it"))).value["label"] is True
    assert (await s.score(_ar("nothing"))).value["label"] is False
