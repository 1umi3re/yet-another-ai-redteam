import pytest
from cryptography.fernet import Fernet
from httpx import AsyncClient, ASGITransport


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
async def test_create_list_delete_target(monkeypatch, tmp_path):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps; deps._STATE = None
    from airedteam.api.app import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        # Ensure tables exist by calling app lifespan startup
        # The ASGITransport should handle this, but let's be explicit
        state = deps.get_state()
        from airedteam.storage.db import make_engine
        from airedteam.storage import models
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        
        h = await _login(c)
        r = await c.post("/api/targets", headers=h, json={
            "name": "t1", "plugin": "openai_compat",
            "params": {"name": "t1", "base_url": "https://x", "model": "m"},
            "secret": {"api_key": "sk-xxx"},
        })
        assert r.status_code == 201
        tid = r.json()["id"]
        r2 = await c.get("/api/targets", headers=h)
        assert any(t["id"] == tid for t in r2.json())
        r3 = await c.delete(f"/api/targets/{tid}", headers=h)
        assert r3.status_code == 204
