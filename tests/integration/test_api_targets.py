import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
async def test_create_list_delete_target(monkeypatch, tmp_path):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        # Ensure tables exist by calling app lifespan startup
        # The ASGITransport should handle this, but let's be explicit
        state = deps.get_state()
        from airedteam.storage import models
        from airedteam.storage.db import make_engine

        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)
        r = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "t1",
                "plugin": "openai_compat",
                "params": {"name": "t1", "base_url": "https://x", "model": "m"},
                "secret": {"api_key": "sk-xxx"},
            },
        )
        assert r.status_code == 201
        tid = r.json()["id"]
        r2 = await c.get("/api/targets", headers=h)
        assert any(t["id"] == tid for t in r2.json())
        r3 = await c.delete(f"/api/targets/{tid}", headers=h)
        assert r3.status_code == 204


@pytest.mark.asyncio
async def test_update_target_limits(monkeypatch, tmp_path):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        from airedteam.storage import models
        from airedteam.storage.db import make_engine

        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)
        r = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "t1",
                "plugin": "openai_compat",
                "params": {"name": "t1", "base_url": "https://x", "model": "m"},
                "secret": {"api_key": "sk-xxx"},
            },
        )
        assert r.status_code == 201
        tid = r.json()["id"]

        updated = await c.patch(
            f"/api/targets/{tid}/limits",
            headers=h,
            json={
                "timeout": 900,
                "max_concurrency": 2,
            },
        )
        assert updated.status_code == 200
        assert updated.json()["params"]["timeout"] == 900
        assert updated.json()["params"]["max_concurrency"] == 2
        assert updated.json()["params"]["base_url"] == "https://x"

        cleared = await c.patch(
            f"/api/targets/{tid}/limits",
            headers=h,
            json={
                "timeout": None,
                "max_concurrency": None,
            },
        )
        assert cleared.status_code == 200
        assert "timeout" not in cleared.json()["params"]
        assert "max_concurrency" not in cleared.json()["params"]


@pytest.mark.asyncio
async def test_update_target_limits_validates_positive_values(monkeypatch, tmp_path):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        from airedteam.storage import models
        from airedteam.storage.db import make_engine

        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)
        r = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "t1",
                "plugin": "openai_compat",
                "params": {"name": "t1", "base_url": "https://x", "model": "m"},
                "secret": {"api_key": "sk-xxx"},
            },
        )
        assert r.status_code == 201
        tid = r.json()["id"]

        bad_timeout = await c.patch(f"/api/targets/{tid}/limits", headers=h, json={"timeout": 0})
        assert bad_timeout.status_code == 422

        bad_concurrency = await c.patch(f"/api/targets/{tid}/limits", headers=h, json={"max_concurrency": 0})
        assert bad_concurrency.status_code == 422
