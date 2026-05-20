import json

import httpx
import pytest
import respx
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
@respx.mock
async def test_converter_preview_resolves_translation_llm(monkeypatch, tmp_path):
    translator_mock = respx.post("https://translator.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "bonjour"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 2},
        })
    )

    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))

    import airedteam.api.deps as deps
    deps._STATE = None
    from airedteam.api.app import create_app
    from airedteam.storage import models
    from airedteam.storage.db import make_engine

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)
        target = await c.post("/api/targets", headers=h, json={
            "name": "translator",
            "plugin": "openai_compat",
            "params": {
                "name": "translator",
                "base_url": "https://translator.example.com/v1",
                "model": "gpt-test",
            },
            "secret": {"api_key": "sk-test"},
        })
        translator_id = target.json()["id"]

        resp = await c.post("/api/converters/preview", headers=h, json={
            "text": "hello",
            "converters": [{
                "plugin": "translation_llm",
                "params": {"translator_config_id": translator_id, "target_language": "French"},
            }],
        })

        assert resp.status_code == 200
        assert resp.json()["original_text"] == "hello"
        assert resp.json()["transformed_text"] == "bonjour"
        assert resp.json()["converter_chain"] == ["translation_llm"]
        assert translator_mock.called
        body = json.loads(translator_mock.calls[0].request.content)
        assert "hello" in str(body)
        assert "French" in str(body)


@pytest.mark.asyncio
@respx.mock
async def test_converter_preview_resolves_llm_converter_config_id(monkeypatch, tmp_path):
    converter_mock = respx.post("https://converter.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "rewritten hello"}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 3},
        })
    )

    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))

    import airedteam.api.deps as deps
    deps._STATE = None
    from airedteam.api.app import create_app
    from airedteam.storage import models
    from airedteam.storage.db import make_engine

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)
        target = await c.post("/api/targets", headers=h, json={
            "name": "converter",
            "plugin": "openai_compat",
            "params": {
                "name": "converter",
                "base_url": "https://converter.example.com/v1",
                "model": "gpt-test",
            },
            "secret": {"api_key": "sk-test"},
        })
        converter_id = target.json()["id"]

        resp = await c.post("/api/converters/preview", headers=h, json={
            "text": "hello",
            "converters": [{
                "plugin": "llm_variation",
                "params": {"converter_config_id": converter_id, "instructions": "keep intent"},
            }],
        })

        assert resp.status_code == 200
        assert resp.json()["transformed_text"] == "rewritten hello"
        assert resp.json()["converter_chain"] == ["llm_variation"]
        assert converter_mock.called
        body = json.loads(converter_mock.calls[0].request.content)
        assert "hello" in str(body)
        assert "keep intent" in str(body)


@pytest.mark.asyncio
@respx.mock
async def test_converter_preview_resolves_garak_lrl_and_paraphrase_configs(monkeypatch, tmp_path):
    translator_mock = respx.post("https://translator.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "yoruba hello"}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 3},
        })
    )
    converter_mock = respx.post("https://converter.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "paraphrased yoruba hello"}}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 3},
        })
    )

    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))

    import airedteam.api.deps as deps
    deps._STATE = None
    from airedteam.api.app import create_app
    from airedteam.storage import models
    from airedteam.storage.db import make_engine

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)
        translator = await c.post("/api/targets", headers=h, json={
            "name": "translator",
            "plugin": "openai_compat",
            "params": {
                "name": "translator",
                "base_url": "https://translator.example.com/v1",
                "model": "gpt-test",
            },
            "secret": {"api_key": "sk-test"},
        })
        converter = await c.post("/api/targets", headers=h, json={
            "name": "converter",
            "plugin": "openai_compat",
            "params": {
                "name": "converter",
                "base_url": "https://converter.example.com/v1",
                "model": "gpt-test",
            },
            "secret": {"api_key": "sk-test"},
        })

        resp = await c.post("/api/converters/preview", headers=h, json={
            "text": "hello",
            "converters": [
                {
                    "plugin": "low_resource_language",
                    "params": {
                        "translator_config_id": translator.json()["id"],
                        "target_language": "Yoruba",
                    },
                },
                {
                    "plugin": "paraphrase_fast",
                    "params": {"converter_config_id": converter.json()["id"]},
                },
            ],
        })

        assert resp.status_code == 200
        assert resp.json()["transformed_text"] == "paraphrased yoruba hello"
        assert resp.json()["converter_chain"] == ["low_resource_language", "paraphrase_fast"]
        assert translator_mock.called
        assert converter_mock.called
        translator_body = json.loads(translator_mock.calls[0].request.content)
        assert "Yoruba" in str(translator_body)
        converter_body = json.loads(converter_mock.calls[0].request.content)
        assert "CPU-friendly" in str(converter_body)
