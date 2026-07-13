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


def test_runspec_accepts_retest_without_dataset_or_executor():
    spec = RunSpec.model_validate(
        {
            "version": 3,
            "name": "retest",
            "targets": [{"config_id": "target-1"}],
            "scorers": [{"plugin": "refusal"}],
            "retest": {
                "mode": "exact_replay",
                "source_target_config_id": "target-1",
                "snapshot_blob_path": "retests/snapshot.json",
                "source_attempt_ids": ["attempt-1"],
            },
        }
    )

    assert spec.dataset is None
    assert spec.retest is not None
    assert spec.retest.mode == "exact_replay"
