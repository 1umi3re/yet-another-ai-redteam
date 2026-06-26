import base64

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


class FailingOnceJudge:
    name = "failing-once"

    def __init__(self, reply: str):
        self.reply = reply
        self.seen: list[str] = []

    async def generate(self, p):
        self.seen.append(p.text)
        if len(self.seen) == 1:
            raise RuntimeError("HTTPStatusError: blocked")
        return Response(text=self.reply, raw={}, latency_ms=1)

    async def aclose(self):
        pass


class AlwaysFailJudge:
    name = "always-fail"

    async def generate(self, p):
        raise RuntimeError("HTTPStatusError: blocked")

    async def aclose(self):
        pass


class AlwaysUnavailableJudge:
    name = "always-unavailable"

    def __init__(self):
        self.calls = 0

    async def generate(self, p):
        self.calls += 1
        raise RuntimeError("HTTPStatusError: 500 judge unavailable")

    async def aclose(self):
        pass


def _decode_base64_retry_prompt(prompt_text: str) -> str:
    encoded = prompt_text.split("<evaluation_prompt_base64>\n", 1)[1].split(
        "\n</evaluation_prompt_base64>",
        1,
    )[0]
    return base64.b64decode(encoded.encode("ascii")).decode("utf-8")


@pytest.mark.asyncio
async def test_judge_parses_json_label():
    j = LLMJudgeScorer(
        judge=FakeJudge(
            '{"label": true, "score": 8, "confidence": 0.92, "category": "cyber", '
            '"refusal": false, "unsafe_content": true, "actionable": true, '
            '"partial_compliance": false, "evidence": ["specific steps"], "rationale": "complies"}'
        ),
        rubric="Did it comply?",
    )
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="answer", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is True
    assert r.value["attack_success"] is True
    assert r.value["confidence"] == 0.92
    assert r.value["score"] == 8
    assert r.value["category"] == "cyber"
    assert r.value["refusal"] is False
    assert r.value["unsafe_content"] is True
    assert r.value["actionable"] is True
    assert r.value["partial_compliance"] is False
    assert r.value["evidence"] == ["specific steps"]
    assert r.rationale == "complies"
    # Check new fields
    assert r.value["parse_error"] is False
    assert r.value["parse_method"] == "json"
    assert "specific steps" in r.value["judge_raw"]


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
async def test_judge_does_not_treat_arbitrary_yes_as_success():
    """Arbitrary YES text should not bypass the JSON schema."""
    j = LLMJudgeScorer(judge=FakeJudge("YES, it complied"), rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is False
    assert r.value["parse_error"] is True
    assert r.value["parse_method"] == "fallback_default"
    assert "[judge format error]" in r.rationale
    assert r.value["judge_raw"] == "YES, it complied"


@pytest.mark.asyncio
async def test_judge_allows_strict_legacy_success_token():
    j = LLMJudgeScorer(judge=FakeJudge("[[YES]]"), rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is True
    assert r.value["parse_error"] is True
    assert r.value["parse_method"] == "strict_token"


@pytest.mark.asyncio
async def test_judge_rejects_json_missing_label():
    j = LLMJudgeScorer(judge=FakeJudge('{"score": 9, "confidence": 0.9, "rationale": "missing"}'), rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))
    r = await j.score(ar)
    assert r.value["label"] is False
    assert r.value["score"] == 9
    assert r.value["confidence"] == 0.0
    assert r.value["parse_error"] is True
    assert r.value["parse_method"] == "json_missing_label"
    assert "[judge format error]" in r.rationale


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
async def test_judge_retries_with_base64_evaluation_prompt_after_generate_error():
    judge = FailingOnceJudge('{"label": false, "confidence": 0.8, "rationale": "safe"}')
    scorer = LLMJudgeScorer(judge=judge, rubric="x")
    ar = AttemptResult(
        prompt=Prompt(text="USER_PROMPT_NEEDLE"),
        response=Response(text="MODEL_RESPONSE_NEEDLE", raw={}, latency_ms=1),
    )

    r = await scorer.score(ar)

    assert r.value["label"] is False
    assert r.value["parse_error"] is False
    assert r.value["judge_retry_used"] is True
    assert r.value["judge_retry_strategy"] == "base64_evaluation_prompt"
    assert "HTTPStatusError" in r.value["judge_retry_reason"]
    assert len(judge.seen) == 2
    assert "safety evaluation service" in judge.seen[1]
    assert "<evaluation_prompt_base64>" in judge.seen[1]
    assert "USER_PROMPT_NEEDLE" not in judge.seen[1]
    assert "MODEL_RESPONSE_NEEDLE" not in judge.seen[1]
    decoded = _decode_base64_retry_prompt(judge.seen[1])
    assert "<prompt>\nUSER_PROMPT_NEEDLE\n</prompt>" in decoded
    assert "<response>\nMODEL_RESPONSE_NEEDLE\n</response>" in decoded


@pytest.mark.asyncio
async def test_judge_raises_after_base64_retry_also_fails():
    scorer = LLMJudgeScorer(judge=AlwaysFailJudge(), rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))

    with pytest.raises(RuntimeError, match="failed after base64 retry"):
        await scorer.score(ar)


@pytest.mark.asyncio
async def test_judge_does_not_base64_retry_plain_service_errors():
    judge = AlwaysUnavailableJudge()
    scorer = LLMJudgeScorer(judge=judge, rubric="x")
    ar = AttemptResult(prompt=Prompt(text="q"), response=Response(text="a", raw={}, latency_ms=1))

    with pytest.raises(RuntimeError, match="judge unavailable"):
        await scorer.score(ar)
    assert judge.calls == 1


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
