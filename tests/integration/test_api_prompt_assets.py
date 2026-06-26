import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
async def test_prompt_asset_api_override_flow(monkeypatch, tmp_path):
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
        listed = await c.get("/api/prompt-assets", headers=h)
        assert listed.status_code == 200
        assert any(a["id"] == "llm_judge.single.v1" for a in listed.json())
        assert any(a["id"] == "llm_judge.single.v2" for a in listed.json())

        custom = await c.post(
            "/api/prompt-assets",
            headers=h,
            json={
                "id": "custom.evaluator.v1",
                "plugin": "custom",
                "purpose": "turn_feedback",
                "category": "Executor",
                "variables": [],
                "template": "Evaluate {goal} with {transcript}",
            },
        )
        assert custom.status_code == 201
        assert custom.json()["is_custom"] is True
        assert custom.json()["category"] == "Executor"
        assert custom.json()["variables"] == ["goal", "transcript"]

        custom_detail = await c.get("/api/prompt-assets/custom.evaluator.v1", headers=h)
        assert custom_detail.status_code == 200
        assert custom_detail.json()["source"] == "custom"

        detail = await c.get("/api/prompt-assets/llm_judge.single.v1", headers=h)
        assert detail.status_code == 200
        assert detail.json()["active_override"] is None

        created = await c.post(
            "/api/prompt-assets/llm_judge.single.v1/overrides",
            headers=h,
            json={"name": "short", "template": "Judge {prompt} / {response} via {rubric}"},
        )
        assert created.status_code == 201
        oid = created.json()["id"]

        active = await c.post(
            "/api/prompt-assets/llm_judge.single.v1/active",
            headers=h,
            json={"override_id": oid},
        )
        assert active.status_code == 200
        assert active.json()["active_override"]["id"] == oid

        updated = await c.patch(
            f"/api/prompt-assets/overrides/{oid}",
            headers=h,
            json={"name": "short v2", "template": "Judge {prompt} -> {response} with {rubric}"},
        )
        assert updated.status_code == 200
        assert updated.json()["name"] == "short v2"

        detail2 = await c.get("/api/prompt-assets/llm_judge.single.v1", headers=h)
        assert detail2.json()["active_override"]["template"] == "Judge {prompt} -> {response} with {rubric}"


@pytest.mark.asyncio
async def test_prompt_snapshot_api(monkeypatch, tmp_path):
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
        async with state.session_factory() as s:
            run = models.Run(name="r", runspec_yaml="{}", status="completed")
            s.add(run)
            await s.flush()
            attempt_path = await state.prompt_assets.write_snapshot(
                run.id,
                "attempt-a1",
                {"snapshots": [{"asset_id": "pair.judge.v1"}]},
            )
            attempt = models.Attempt(
                id="a1",
                run_id=run.id,
                target_id="t",
                target_name="t",
                prompt_text="p",
                prompt_snapshot_blob_path=attempt_path,
            )
            s.add(attempt)
            await s.flush()
            score_path = await state.prompt_assets.write_snapshot(
                run.id,
                "score-s1",
                {"asset_id": "llm_judge.single.v1"},
            )
            s.add(
                models.Score(
                    id="s1",
                    attempt_id=attempt.id,
                    scorer="llm_judge",
                    value_json={"label": True},
                    prompt_snapshot_blob_path=score_path,
                )
            )
            await s.commit()
            run_id = run.id

        attempts = await c.get(f"/api/runs/{run_id}/attempts", headers=h)
        assert attempts.json()[0]["prompt_snapshot_blob_path"] == attempt_path
        scores = await c.get(f"/api/runs/{run_id}/scores", headers=h)
        assert scores.json()[0]["prompt_snapshot_blob_path"] == score_path

        attempt_snapshot = await c.get(f"/api/runs/{run_id}/attempts/a1/prompt-snapshot", headers=h)
        assert attempt_snapshot.status_code == 200
        assert attempt_snapshot.json()["snapshots"][0]["asset_id"] == "pair.judge.v1"
        score_snapshot = await c.get(f"/api/runs/{run_id}/scores/s1/prompt-snapshot", headers=h)
        assert score_snapshot.status_code == 200
        assert score_snapshot.json()["asset_id"] == "llm_judge.single.v1"
