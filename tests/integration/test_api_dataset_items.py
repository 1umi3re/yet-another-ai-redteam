import json

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
async def test_dataset_items_preview(monkeypatch, tmp_path):
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
        files = {
            "file": (
                "items.json",
                json.dumps({"items": [
                    {"id": "p1", "prompt": "Prompt one", "category": "a"},
                    {"id": "p2", "prompt": "Prompt two", "category": "b"},
                ]}),
                "application/json",
            )
        }
        created = await c.post("/api/datasets/upload", headers=h, data={"name": "bench"}, files=files)
        ds_id = created.json()["id"]

        items = await c.get(f"/api/datasets/{ds_id}/items?limit=1", headers=h)
        assert items.status_code == 200
        assert items.json()["items"] == [{
            "id": "p1",
            "text": "Prompt one",
            "metadata": {"id": "p1", "category": "a"},
        }]
        assert items.json()["total_returned"] == 1
