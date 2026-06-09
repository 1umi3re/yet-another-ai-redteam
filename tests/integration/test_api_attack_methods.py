import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
async def test_attack_method_category_api_crud_and_plugin_mapping(monkeypatch, tmp_path):
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
    state = deps.get_state()
    eng = make_engine(state.settings.database_url)
    async with eng.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        h = await _login(c)

        listed = await c.get("/api/attack-method-categories", headers=h)
        assert listed.status_code == 200
        body = listed.json()
        assert any(category["id"] == "encoding_obfuscation" for category in body["categories"])
        assert any(
            mapping["executor_kind"] == "converter_method"
            and mapping["executor_name"] == "base64"
            and mapping["category_id"] == "encoding_obfuscation"
            for mapping in body["mappings"]
        )

        created = await c.post(
            "/api/attack-method-categories",
            headers=h,
            json={
                "id": "custom_strategy",
                "name": "Custom strategy",
                "alias": "custom",
                "type": "Custom",
                "description": "temporary",
                "display_order": 500,
            },
        )
        assert created.status_code == 201
        assert created.json()["id"] == "custom_strategy"

        mapped = await c.put(
            "/api/attack-method-categories/mappings/converter_method/base64",
            headers=h,
            json={"category_id": "custom_strategy", "technical_category": "encoding"},
        )
        assert mapped.status_code == 200
        assert mapped.json()["category_id"] == "custom_strategy"

        plugins = await c.get("/api/plugins", headers=h)
        assert plugins.json()["executor_attack_categories"]["base64"] == "custom_strategy"

        blocked = await c.delete("/api/attack-method-categories/custom_strategy", headers=h)
        assert blocked.status_code == 400
        assert "still has mappings" in blocked.json()["detail"]

        restored = await c.put(
            "/api/attack-method-categories/mappings/converter_method/base64",
            headers=h,
            json={"category_id": "encoding_obfuscation", "technical_category": "encoding"},
        )
        assert restored.status_code == 200

        deleted = await c.delete("/api/attack-method-categories/custom_strategy", headers=h)
        assert deleted.status_code == 204
