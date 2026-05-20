from airedteam.engine.factory import build_converter, build_executor, build_scorer


def test_build_converter_identity():
    c = build_converter({"plugin": "identity", "params": {}})
    assert c.name == "identity"


def test_build_executor_single_turn():
    e = build_executor({"plugin": "single_turn", "params": {}})
    assert e.name == "single_turn"


def test_build_executor_best_of_n():
    e = build_executor({"plugin": "best_of_n", "params": {"attempts": 2}})
    assert e.name == "best_of_n"
    assert e.attempts == 2


def test_build_executor_jailbreak_iterative_requires_attacker_and_judge():
    try:
        build_executor({"plugin": "jailbreak_iterative", "params": {}})
    except ValueError as exc:
        assert "attacker" in str(exc)
    else:
        raise AssertionError("jailbreak_iterative should require attacker and judge")


def test_build_scorer_refusal():
    s = build_scorer({"plugin": "refusal", "params": {}})
    assert s.name == "refusal"
