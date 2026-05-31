import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_login_success_and_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/api/login", json={"password": "letmein"})
        assert r.status_code == 200 and "token" in r.json()
        bad = await c.post("/api/login", json={"password": "wrong"})
        assert bad.status_code == 401
