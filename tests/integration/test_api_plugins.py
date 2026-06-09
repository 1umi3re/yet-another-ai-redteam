import tomllib
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
async def test_list_plugins_and_scenarios(monkeypatch, tmp_path):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        h = await _login(c)
        r = await c.get("/api/plugins", headers=h)
        body = r.json()
        assert "openai_compat" in body["targets"]
        assert "refusal" in body["scorers"]
        assert "general_multi_turn" in body["general_multi_turn_executors"]
        expected_converters = set(
            tomllib.loads(Path("pyproject.toml").read_text())["project"]["entry-points"]["airedteam.converters"]
        )
        removed_aliases = {
            "alter_sentence_structure",
            "ansi_attack",
            "audio_encoding",
            "base_image_text",
            "base_image_to_image",
            "change_style",
            "char_spacing",
            "charswap_attack",
            "codechameleon",
            "emoji",
            "expand",
            "flip",
            "generate_similar",
            "image_encoding",
            "insert_meaningless_characters",
            "llm_generic_text",
            "malicious_question_generator",
            "markdown_wrap",
            "math_problem",
            "misspell_sensitive_words",
            "persuasion",
            "random_capital_letters",
            "random_translation",
            "rephrase",
            "reverse",
            "scientific_translation",
            "shorten",
            "text_jailbreak",
            "tone",
            "toxic_sentence_generator",
            "translation",
            "unicode_confusable",
            "unicode_sub",
            "url",
            "variation",
            "video_encoding",
        }
        assert removed_aliases.isdisjoint(body["converters"])
        assert removed_aliases.isdisjoint(body["params"]["converters"])
        for converter in expected_converters:
            assert converter in body["converters"]
            assert converter in body["params"]["converters"]
        missing_converter_defaults = []
        for plugin, schema in body["params"]["converters"].items():
            for name, spec in schema.items():
                if spec.get("type") == "target_ref":
                    continue
                if "default" not in spec:
                    missing_converter_defaults.append(f"{plugin}.{name}")
        assert missing_converter_defaults == []
        converter_params = body["params"]["converters"]
        assert converter_params["llm_variation"]["converter_config_id"]["type"] == "target_ref"
        llm_variation_prompt = converter_params["llm_variation"]["prompt_asset_id"]
        assert llm_variation_prompt["type"] == "prompt_asset_ref"
        assert llm_variation_prompt["default"] == "llm_variation.rewrite.v1"
        assert llm_variation_prompt["purpose_exclude"] == "attack_template"
        assert converter_params["translation_llm"]["prompt_asset_id"]["default"] == "translation_llm.translate.v1"
        assert body["converter_categories"]["base64"] == "encoding"
        assert body["converter_categories"]["leetspeak"] == "obfuscation"
        assert body["converter_categories"]["prefix"] == "prompt_framing"
        template_jailbreak_asset = converter_params["template_jailbreak"]["attack_template_asset_id"]
        assert template_jailbreak_asset["purpose_filter"] == "attack_template"
        assert "best_of_n" in body["executors"]
        assert body["params"]["executors"]["best_of_n"]["attempts"]["default"] == "5"
        assert "base64" in body["executor_methods"]
        assert body["executor_method_categories"]["base64"] == "encoding"
        assert body["params"]["executor_methods"]["base64"]["wrap"]["default"] is True
        assert body["executor_language_support"]["base64"] == ["en"]
        assert body["executor_language_support"]["single_turn"] == ["en", "zh"]
        assert body["executor_language_support"]["general_multi_turn"] == ["en", "zh"]
        assert "jailbreak_iterative" in body["executors"]
        jailbreak_params = body["params"]["executors"]["jailbreak_iterative"]
        assert jailbreak_params["judge_config_id"]["type"] == "target_ref"
        rs = await c.get("/api/scenarios", headers=h)
        scenarios = rs.json()
        assert any(s["id"] == "owasp_llm_top10_jailbreak" for s in scenarios)
        encoding = next(s for s in scenarios if s["id"] == "encoding_bypass")
        assert encoding["level"] == "basic"
        assert encoding["requirements"] == []
        pair = next(s for s in scenarios if s["id"] == "pair_iterative")
        assert pair["level"] == "advanced"
        assert {req["id"] for req in pair["requirements"]} == {"attacker_config_id", "judge_config_id"}

        rendered = await c.post(
            "/api/scenarios/encoding_bypass/runspec",
            headers=h,
            json={"target_config_id": "target-1", "dataset_config_id": "dataset-1"},
        )
        assert rendered.status_code == 200
        spec = rendered.json()
        assert spec["scenario"] == "encoding_bypass"
        assert spec["targets"] == [{"config_id": "target-1"}]
        assert spec["dataset"] == {"config_id": "dataset-1"}
        assert [c["plugin"] for c in spec["converters"]] == ["base64", "rot13", "hex", "unicode_escape"]

        missing_helper = await c.post(
            "/api/scenarios/pair_iterative/runspec",
            headers=h,
            json={"target_config_id": "target-1", "dataset_config_id": "dataset-1"},
        )
        assert missing_helper.status_code == 400
        assert "attacker_config_id" in missing_helper.json()["detail"]


def test_general_multi_turn_variant_plugin_schema_uses_variant_defaults():
    from airedteam.api.routers.plugins import (
        general_multi_turn_executor_names,
        plugin_param_schemas,
    )
    from airedteam.builtins.executors.general_multi_turn import make_general_multi_turn_executor
    from airedteam.core.registry import Registry

    registry = Registry()
    registry.register(
        "executors",
        "variant_multi_turn_schema",
        make_general_multi_turn_executor(
            "variant_multi_turn_schema",
            attacker_prompt_asset_id="variant.attacker.v1",
            evaluator_prompt_asset_id="variant.evaluator.v1",
            judger_prompt_asset_id="variant.judger.v1",
        ),
    )

    schema = plugin_param_schemas(registry)["executors"]["variant_multi_turn_schema"]

    assert "variant_multi_turn_schema" in general_multi_turn_executor_names(registry)
    assert schema["attacker_prompt_asset_id"]["default"] == "variant.attacker.v1"
    assert schema["evaluator_prompt_asset_id"]["default"] == "variant.evaluator.v1"
    assert schema["judger_prompt_asset_id"]["default"] == "variant.judger.v1"
