from airedteam.builtins.scenarios.owasp_llm_top10_jailbreak import scenario, bundled_prompts_json
import json


def test_scenario_describes_runspec_template():
    spec = scenario.runspec_template(target_config_id="abc")
    assert spec["name"].startswith("OWASP")
    assert spec["targets"][0]["config_id"] == "abc"
    assert spec["dataset"]["plugin"] == "json_upload"
    assert any(s["plugin"] == "refusal" for s in spec["scorers"])


def test_scenario_metadata():
    assert scenario.id == "owasp_llm_top10_jailbreak"
    assert "jailbreak" in scenario.tags


def test_bundled_prompts_parse():
    data = json.loads(bundled_prompts_json().decode())
    assert len(data["items"]) >= 5
