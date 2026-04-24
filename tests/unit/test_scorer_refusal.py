import pytest
from airedteam.builtins.scorers.refusal import RefusalScorer
from airedteam.core.types import AttemptResult, Prompt, Response


def _ar(t): return AttemptResult(prompt=Prompt(text="x"), response=Response(text=t, raw={}, latency_ms=1))


@pytest.mark.asyncio
async def test_refusal_phrase_detected():
    s = RefusalScorer()
    r = await s.score(_ar("I'm sorry, but I can't help with that."))
    assert r.value["label"] is True
    assert r.value["attack_success"] is False


@pytest.mark.asyncio
async def test_compliance_returned_false():
    s = RefusalScorer()
    r = await s.score(_ar("Sure! Here are the steps: 1. ..."))
    assert r.value["label"] is False
    assert r.value["attack_success"] is True
