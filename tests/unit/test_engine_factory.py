from airedteam.engine.factory import build_converter, build_executor, build_scorer


def test_build_converter_identity():
    c = build_converter({"plugin": "identity", "params": {}})
    assert c.name == "identity"


def test_build_executor_single_turn():
    e = build_executor({"plugin": "single_turn", "params": {}})
    assert e.name == "single_turn"


def test_build_scorer_refusal():
    s = build_scorer({"plugin": "refusal", "params": {}})
    assert s.name == "refusal"
