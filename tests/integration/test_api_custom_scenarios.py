import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
async def test_create_list_and_render_custom_scenario(monkeypatch, tmp_path):
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
        payload = {
            "name": "Saved pipeline",
            "description": "Regression pipeline",
            "tags": ["custom", "regression"],
            "template": {
                "version": 2,
                "name": "must not persist",
                "targets": [{"config_id": "old-target"}],
                "dataset": {"config_id": "old-dataset"},
                "executors": [
                    {"kind": "executor", "plugin": "single_turn", "params": {}},
                    {"kind": "converter_method", "plugin": "base64", "params": {"wrap": False}},
                ],
                "scorers": [{"plugin": "refusal", "params": {}}],
                "sampling": {"limit": 3, "shuffle": True, "seed": 42},
                "timeout_seconds": 120,
            },
        }

        created = await c.post("/api/scenarios/custom", headers=h, json=payload)
        assert created.status_code == 201
        body = created.json()
        assert body["id"].startswith("custom:")
        assert body["title"] == "Saved pipeline"
        assert body["source"] == "custom"
        assert body["tags"] == ["custom", "regression"]

        scenarios = (await c.get("/api/scenarios", headers=h)).json()
        listed = next(s for s in scenarios if s["id"] == body["id"])
        assert listed["title"] == "Saved pipeline"
        assert listed["level"] == "custom"

        rendered = await c.post(
            f"/api/scenarios/{body['id']}/runspec",
            headers=h,
            json={"target_config_id": "new-target", "dataset_config_id": "new-dataset"},
        )
        assert rendered.status_code == 200
        spec = rendered.json()
        assert spec["name"] == "Saved pipeline"
        assert spec["scenario"] == body["id"]
        assert spec["targets"] == [{"config_id": "new-target"}]
        assert spec["dataset"] == {"config_id": "new-dataset"}
        assert [ref["plugin"] for ref in spec["executors"]] == ["single_turn", "base64"]
        assert spec["executors"][1]["kind"] == "converter_method"
        assert spec["executors"][1]["params"] == {"wrap": False}
        assert spec["scorers"] == [{"plugin": "refusal", "params": {}}]
        assert spec["sampling"] == {"limit": 3, "shuffle": True, "seed": 42}
        assert spec["timeout_seconds"] == 120
