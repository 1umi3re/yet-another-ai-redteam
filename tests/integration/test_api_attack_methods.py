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


@pytest.mark.asyncio
async def test_attack_method_prompt_template_api_crud(monkeypatch, tmp_path):
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

        detail = await c.get("/api/attack-methods/converter_method/prefix/templates", headers=h)
        assert detail.status_code == 200
        body = detail.json()
        assert body["is_template_backed"] is True
        assert body["default_asset_id"] == "attack_method.prefix.default.v1"
        assert body["templates"][0]["is_builtin"] is True
        assert body["templates"][0]["is_active"] is True

        created = await c.post(
            "/api/attack-methods/converter_method/prefix/templates",
            headers=h,
            json={"name": "workspace prefix", "template": "WORKSPACE {prefix}|{prompt}", "active": True},
        )
        assert created.status_code == 201
        override_id = created.json()["id"]

        active = await c.get("/api/attack-methods/converter_method/prefix/templates", headers=h)
        active_templates = active.json()["templates"]
        assert any(t["id"] == override_id and t["is_active"] for t in active_templates)
        assert active.json()["active_override"]["id"] == override_id

        updated = await c.patch(
            f"/api/attack-methods/templates/{override_id}",
            headers=h,
            json={"name": "edited prefix", "template": "EDITED {prefix}|{prompt}"},
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "edited prefix"

        reverted = await c.post(
            "/api/attack-methods/converter_method/prefix/templates/active",
            headers=h,
            json={"override_id": None},
        )
        assert reverted.status_code == 200
        assert reverted.json()["active_override"] is None

        deleted = await c.delete(f"/api/attack-methods/templates/{override_id}", headers=h)
        assert deleted.status_code == 204

        missing = await c.delete(f"/api/attack-methods/templates/{override_id}", headers=h)
        assert missing.status_code == 404

        unsupported = await c.get("/api/attack-methods/converter_method/meta_agent/templates", headers=h)
        assert unsupported.status_code == 200
        assert unsupported.json()["is_template_backed"] is False


@pytest.mark.asyncio
async def test_attack_method_template_detail_lists_imported_method_templates(monkeypatch, tmp_path):
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

        detail = await c.get("/api/attack-methods/converter_method/dan/templates", headers=h)
        assert detail.status_code == 200
        body = detail.json()

        assert body["is_template_backed"] is True
        assert body["default_asset_id"] == "attack_method.dan.default.v1"
        template_asset_ids = [template["asset_id"] for template in body["templates"]]
        assert len(template_asset_ids) == len(set(template_asset_ids))
        assert template_asset_ids[0] == "attack_method.dan.default.v1"
        assert "attack_method.dan.template.better_dan.v1" in template_asset_ids
        assert "attack_method.dan.template.cosmos_dan.v1" in template_asset_ids
        assert "attack_method.dan.template.superior_dan.v1" in template_asset_ids
