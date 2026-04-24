import pytest
from airedteam.builtins.scorers.llm_judge import LLMJudgeScorer
from airedteam.core.types import AttemptResult, Prompt, Response


class FakeJudge:
    name = "fake"
    def __init__(self, reply: str): self.reply = reply
    async def generate(self, p):
        return Response(text=self.reply, raw={}, latency_ms=1)
    async def aclose(self): pass


@pytest.mark.asyncio
async def test_judge_parses_json_label():
    j = LLMJudgeScorer(judge=FakeJudge('{"label": true, "confidence": 0.92, "rationale": "complies"}'), rubric="Did it comply?")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="answer", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is True
    assert r.value["attack_success"] is True
    assert r.value["confidence"] == 0.92
    assert r.rationale == "complies"


@pytest.mark.asyncio
async def test_judge_refusal_maps_to_attack_failure():
    j = LLMJudgeScorer(judge=FakeJudge('{"label": false, "confidence": 0.8, "rationale": "refused"}'), rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is False
    assert r.value["attack_success"] is False


@pytest.mark.asyncio
async def test_judge_handles_non_json():
    j = LLMJudgeScorer(judge=FakeJudge("YES, it complied"), rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is True


def test_judge_requires_judge():
    with pytest.raises(ValueError):
        LLMJudgeScorer(judge=None, rubric="x")


@pytest.mark.asyncio
async def test_judge_uses_default_rubric_when_none():
    j = LLMJudgeScorer(judge=FakeJudge('{"label": false, "confidence": 0.7}'))
    assert "harmful" in j.rubric or "label" in j.rubric.lower() or j.rubric
