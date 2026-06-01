from __future__ import annotations

from importlib.resources import files

from airedteam.core.scenario import Scenario


def _runspec_template(
    *,
    target_config_id: str | None = None,
    target_inline: dict | None = None,
    dataset_config_id: str | None = None,
    dataset_blob_path: str | None = None,
) -> dict:
    if not (target_config_id or target_inline):
        raise ValueError("target_config_id or target_inline required")
    if target_config_id:
        target = {"config_id": target_config_id}
    else:
        target = {"plugin": target_inline["plugin"], "params": target_inline["params"]}
    if dataset_config_id:
        dataset = {"config_id": dataset_config_id}
    else:
        dataset = {
            "plugin": "json_upload",
            "params": {"blob_path": dataset_blob_path or "scenarios/owasp_llm_top10_jailbreak.json"},
        }
    return {
        "name": "OWASP LLM Top10 - Jailbreak",
        "scenario": "owasp_llm_top10_jailbreak",
        "targets": [target],
        "dataset": dataset,
        "converters": [],
        "executor": {"plugin": "single_turn"},
        "scorers": [{"plugin": "refusal"}],
        "concurrency": 4,
    }


def bundled_prompts_json() -> bytes:
    return files("airedteam.builtins.scenarios").joinpath("owasp_llm_top10_jailbreak.json").read_bytes()


scenario = Scenario(
    id="owasp_llm_top10_jailbreak",
    title="OWASP LLM Top10 - Jailbreak (LLM01)",
    description="Bundled jailbreak/prompt-injection probes inspired by OWASP LLM Top10 LLM01.",
    tags=["jailbreak", "owasp", "LLM01"],
    level="basic",
    runspec_template=_runspec_template,
)
