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
