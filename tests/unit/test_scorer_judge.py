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
    assert r.value["confidence"] == 0.92
    assert r.rationale == "complies"


@pytest.mark.asyncio
async def test_judge_handles_non_json():
    j = LLMJudgeScorer(judge=FakeJudge("YES, it complied"), rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is True
