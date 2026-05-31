import pytest

from airedteam.builtins.scorers.llm_judge import LLMJudgeScorer
from airedteam.core.types import AttemptResult, Prompt, Response


class FakeJudge:
    name = "fake"

    def __init__(self, reply: str):
        self.reply = reply

    async def generate(self, p):
        return Response(text=self.reply, raw={}, latency_ms=1)

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_judge_parses_json_label():
    j = LLMJudgeScorer(
        judge=FakeJudge('{"label": true, "confidence": 0.92, "rationale": "complies"}'), rubric="Did it comply?"
    )
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="answer", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is True
    assert r.value["attack_success"] is True
    assert r.value["confidence"] == 0.92
    assert r.rationale == "complies"
    # Check new fields
    assert r.value["parse_error"] is False
    assert r.value["parse_method"] == "json"
    assert r.value["judge_raw"] == '{"label": true, "confidence": 0.92, "rationale": "complies"}'


@pytest.mark.asyncio
async def test_judge_refusal_maps_to_attack_failure():
    j = LLMJudgeScorer(judge=FakeJudge('{"label": false, "confidence": 0.8, "rationale": "refused"}'), rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is False
    assert r.value["attack_success"] is False
    assert r.value["parse_error"] is False
    assert r.value["parse_method"] == "json"


@pytest.mark.asyncio
async def test_judge_handles_non_json_yes():
    """Test heuristic fallback for YES keyword."""
    j = LLMJudgeScorer(judge=FakeJudge("YES, it complied"), rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is True
    assert r.value["parse_error"] is True
    assert r.value["parse_method"] == "heuristic_yes_no"
    assert "[judge format error]" in r.rationale
    assert r.value["judge_raw"] == "YES, it complied"


@pytest.mark.asyncio
async def test_judge_handles_malformed_json():
    """Test fallback when output is not valid JSON and has no YES/TRUE."""
    j = LLMJudgeScorer(judge=FakeJudge("Some random text without keywords"), rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is False  # Default fallback
    assert r.value["confidence"] == 0.0
    assert r.value["parse_error"] is True
    assert r.value["parse_method"] == "fallback_default"
    assert "[judge format error]" in r.rationale
    assert r.value["judge_raw"] == "Some random text without keywords"


@pytest.mark.asyncio
async def test_judge_stores_full_raw_output():
    """Test that judge_raw contains full output, not truncated."""
    long_output = "A" * 1000  # 1000 chars
    j = LLMJudgeScorer(judge=FakeJudge(long_output), rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert len(r.value["judge_raw"]) == 1000
    assert r.value["judge_raw"] == long_output


def test_judge_requires_judge():
    with pytest.raises(ValueError):
        LLMJudgeScorer(judge=None, rubric="x")


@pytest.mark.asyncio
async def test_judge_uses_default_rubric_when_none():
    j = LLMJudgeScorer(judge=FakeJudge('{"label": false, "confidence": 0.7}'))
    assert "harmful" in j.rubric or "label" in j.rubric.lower() or j.rubric
