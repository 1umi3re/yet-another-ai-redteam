import httpx
import pytest
import respx
from httpx import ASGITransport, AsyncClient


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
@respx.mock
async def test_owasp_scenario_via_api(monkeypatch, tmp_path):
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "I cannot help with that"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
    )
    from cryptography.fernet import Fernet

    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app
    from airedteam.builtins.scenarios.owasp_llm_top10_jailbreak import (
        bundled_prompts_json,
        scenario,
    )

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        from airedteam.storage import models
        from airedteam.storage.db import make_engine

        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        h = await _login(c)
        t = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "t1",
                "plugin": "openai_compat",
                "params": {"name": "t1", "base_url": "https://api.example.com/v1", "model": "m"},
                "secret": {"api_key": "sk"},
            },
        )
        tid = t.json()["id"]
        ds = await c.post(
            "/api/datasets/upload",
            headers=h,
            files={"file": ("owasp.json", bundled_prompts_json(), "application/json")},
            data={"name": "owasp"},
        )
        did = ds.json()["id"]
        spec = scenario.runspec_template(target_config_id=tid)
        spec["dataset"] = {"config_id": did}
        cr = await c.post("/api/runs", headers=h, json={"name": "e2e", "runspec": spec})
        rid = cr.json()["id"]
        await c.post(f"/api/runs/{rid}/start", headers=h)
        import asyncio

        s = None
        for _ in range(200):
            s = (await c.get(f"/api/runs/{rid}", headers=h)).json()
            if s["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.05)
        assert s["status"] == "completed", s
        attempts = (await c.get(f"/api/runs/{rid}/attempts", headers=h)).json()
        assert len(attempts) >= 5
        scores = (await c.get(f"/api/runs/{rid}/scores", headers=h)).json()
        assert all(sc["value"]["label"] is True for sc in scores)
