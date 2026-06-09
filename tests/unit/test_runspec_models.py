from airedteam.runspec.models import RunSpec


def test_runspec_validates_minimal():
    s = RunSpec.model_validate(
        {
            "name": "r",
            "targets": [{"config_id": "t1"}],
            "dataset": {"config_id": "d1"},
            "executor": {"plugin": "single_turn"},
            "scorers": [{"plugin": "refusal"}],
        }
    )
    assert s.version == 1
    assert s.concurrency == 4
    assert s.targets[0].config_id == "t1"
    assert s.executor.plugin == "single_turn"
    assert s.converters == []


def test_runspec_accepts_executor_list_v2():
    s = RunSpec.model_validate(
        {
            "version": 2,
            "name": "r",
            "targets": [{"config_id": "t1"}],
            "dataset": {"config_id": "d1"},
            "executors": [
                {"kind": "executor", "plugin": "single_turn"},
                {"kind": "converter_method", "plugin": "base64", "params": {"wrap": False}},
            ],
            "scorers": [{"plugin": "refusal"}],
        }
    )

    assert s.version == 2
    assert [executor.kind for executor in s.executors] == ["executor", "converter_method"]
    assert [executor.plugin for executor in s.executors] == ["single_turn", "base64"]
