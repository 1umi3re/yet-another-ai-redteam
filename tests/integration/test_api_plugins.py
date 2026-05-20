import tomllib
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from httpx import AsyncClient, ASGITransport


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
async def test_list_plugins_and_scenarios(monkeypatch, tmp_path):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps; deps._STATE = None
    from airedteam.api.app import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        h = await _login(c)
        r = await c.get("/api/plugins", headers=h)
        body = r.json()
        assert "openai_compat" in body["targets"]
        assert "refusal" in body["scorers"]
        expected_converters = set(
            tomllib.loads(Path("pyproject.toml").read_text())["project"]["entry-points"][
                "airedteam.converters"
            ]
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
        assert body["params"]["converters"]["llm_variation"]["converter_config_id"]["type"] == "target_ref"
        assert body["converter_categories"]["base64"] == "encoding"
        assert body["converter_categories"]["leetspeak"] == "obfuscation"
        assert body["converter_categories"]["prefix"] == "prompt_framing"
        assert "best_of_n" in body["executors"]
        assert body["params"]["executors"]["best_of_n"]["attempts"]["default"] == "5"
        assert "jailbreak_iterative" in body["executors"]
        assert body["params"]["executors"]["jailbreak_iterative"]["judge_config_id"]["type"] == "target_ref"
        rs = await c.get("/api/scenarios", headers=h)
        assert any(s["id"] == "owasp_llm_top10_jailbreak" for s in rs.json())
