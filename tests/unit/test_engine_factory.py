from airedteam.core.registry import default_registry
from airedteam.engine.factory import build_converter, build_executor, build_scorer, build_target


def test_build_target_filters_runtime_params_but_keeps_timeout():
    class RuntimeParamTarget:
        def __init__(self, *, name: str, timeout: float) -> None:
            self.name = name
            self.timeout = timeout

    default_registry().register("targets", "runtime_param_target", RuntimeParamTarget)

    t = build_target(
        {
            "plugin": "runtime_param_target",
            "params": {
                "name": "t1",
                "timeout": 123.0,
                "max_concurrency": 2,
                "max_input_chars": 200,
                "input_limit_unit": "characters",
            },
        }
    )

    assert t.name == "t1"
    assert t.timeout == 123.0


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


def test_build_executor_split():
    e = build_executor({"plugin": "split_executor", "params": {}})
    assert e.name == "split_executor"


def test_build_executor_jailbreak_iterative_requires_attacker_and_judge():
    try:
        build_executor({"plugin": "jailbreak_iterative", "params": {}})
    except ValueError as exc:
        assert "attacker" in str(exc)
    else:
        raise AssertionError("jailbreak_iterative should require attacker and judge")


def test_build_executor_general_multi_turn_requires_role_targets():
    try:
        build_executor({"plugin": "general_multi_turn", "params": {}})
    except ValueError as exc:
        assert "attacker" in str(exc)
    else:
        raise AssertionError("general_multi_turn should require role targets")


def test_build_scorer_refusal():
    s = build_scorer({"plugin": "refusal", "params": {}})
    assert s.name == "refusal"
