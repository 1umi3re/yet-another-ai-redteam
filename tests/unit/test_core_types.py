from airedteam.core.types import AttemptResult, Prompt, Response, ScoreResult


def test_prompt_immutable():
    p = Prompt(text="hi", metadata={"id": "x"})
    assert p.text == "hi"
    assert p.metadata["id"] == "x"


def test_response_fields():
    r = Response(text="hello", raw={"choices": []}, latency_ms=120, tokens_in=3, tokens_out=2)
    assert r.text == "hello"
    assert r.latency_ms == 120


def test_attempt_result_status_default_completed():
    a = AttemptResult(prompt=Prompt(text="x"), response=Response(text="y", raw={}, latency_ms=1))
    assert a.status == "completed"
    assert a.error is None


def test_score_result_value_can_be_dict():
    s = ScoreResult(scorer="x", value={"label": True, "confidence": 0.9})
    assert s.value["label"] is True
