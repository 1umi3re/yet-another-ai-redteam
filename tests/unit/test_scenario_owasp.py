import json

from airedteam.builtins.scenarios import presets
from airedteam.builtins.scenarios.owasp_llm_top10_jailbreak import bundled_prompts_json, scenario


def test_scenario_describes_runspec_template():
    spec = scenario.runspec_template(target_config_id="abc", dataset_config_id="ds1")
    assert spec["name"].startswith("OWASP")
    assert spec["targets"][0]["config_id"] == "abc"
    assert spec["dataset"]["config_id"] == "ds1"
    assert any(s["plugin"] == "refusal" for s in spec["scorers"])


def test_scenario_metadata():
    assert scenario.id == "owasp_llm_top10_jailbreak"
    assert "jailbreak" in scenario.tags


def test_bundled_prompts_parse():
    data = json.loads(bundled_prompts_json().decode())
    assert len(data["items"]) >= 5


def test_basic_preset_scenarios_are_dataset_driven_and_zero_extra_config():
    scenarios = [
        presets.direct_safety_baseline,
        presets.encoding_bypass,
        presets.obfuscation_robustness,
        presets.prompt_framing_jailbreak,
        presets.structured_injection,
        presets.input_limited_split,
    ]

    for preset in scenarios:
        spec = preset.runspec_template(target_config_id="target-1", dataset_config_id="dataset-1")
        assert preset.level == "basic"
        assert preset.requirements == []
        assert spec["targets"] == [{"config_id": "target-1"}]
        assert spec["dataset"] == {"config_id": "dataset-1"}
        assert spec["scorers"] == [{"plugin": "refusal"}]
        assert spec["scenario"] == preset.id

    assert presets.input_limited_split.runspec_template(
        target_config_id="target-1", dataset_config_id="dataset-1"
    )["executor"]["plugin"] == "split_executor"


def test_advanced_preset_scenarios_require_helper_targets():
    try:
        presets.crescendo_adaptive.runspec_template(target_config_id="target-1", dataset_config_id="dataset-1")
    except ValueError as exc:
        assert "attacker_config_id" in str(exc)
    else:
        raise AssertionError("crescendo_adaptive should require attacker_config_id")

    pair_spec = presets.pair_iterative.runspec_template(
        target_config_id="target-1",
        dataset_config_id="dataset-1",
        attacker_config_id="attacker-1",
        judge_config_id="judge-1",
    )
    assert presets.pair_iterative.level == "advanced"
    assert {req.id for req in presets.pair_iterative.requirements} == {"attacker_config_id", "judge_config_id"}
    assert pair_spec["executor"]["plugin"] == "pair"
    assert pair_spec["executor"]["params"]["attacker_config_id"] == "attacker-1"
    assert pair_spec["executor"]["params"]["judge_config_id"] == "judge-1"
