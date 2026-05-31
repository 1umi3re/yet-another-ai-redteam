import json

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
async def test_annotate_score(monkeypatch, tmp_path):
    """Test annotating a score with reviewer_label and notes."""
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))

    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app
    from airedteam.storage import models

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        from airedteam.storage.db import make_engine

        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)

        # Create target
        t = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "test_target",
                "plugin": "openai_compat",
                "params": {"name": "test_target", "base_url": "https://test.example.com/v1", "model": "gpt-test"},
                "secret": {"api_key": "sk-test"},
            },
        )
        tid = t.json()["id"]

        # Create run + attempt + score directly via SQLAlchemy
        async with state.session_factory() as s:
            run = models.Run(
                name="Test Run",
                runspec_yaml=json.dumps({"target_id": tid}),
                status="completed",
                kind="automated",
            )
            s.add(run)
            await s.flush()

            att = models.Attempt(
                id="test-att-1",
                run_id=run.id,
                target_id=tid,
                target_name="test_target",
                prompt_text="Test prompt",
                response_text="Test response",
            )
            s.add(att)
            await s.flush()

            score = models.Score(
                id="test-score-1",
                attempt_id=att.id,
                scorer="refusal",
                value_json={"label": True, "confidence": 0.95},
                rationale="Detected refusal pattern",
            )
            s.add(score)
            await s.commit()
            rid = run.id
            sid = score.id

        # Verify score has no reviewer fields initially
        scores_before = await c.get(f"/api/runs/{rid}/scores", headers=h)
        assert scores_before.status_code == 200
        score_data = scores_before.json()[0]
        assert score_data["id"] == sid
        assert score_data["reviewer_label"] is None
        assert score_data["reviewer_notes"] is None
        assert score_data["reviewer_id"] is None
        assert score_data["reviewed_at"] is None

        # Annotate the score
        r1 = await c.patch(
            f"/api/runs/{rid}/scores/{sid}",
            headers=h,
            json={"reviewer_label": False, "reviewer_notes": "Actually not a refusal, it's compliant"},
        )
        assert r1.status_code == 200
        annotated = r1.json()
        assert annotated["id"] == sid
        assert annotated["reviewer_label"] is False
        assert annotated["reviewer_notes"] == "Actually not a refusal, it's compliant"
        assert annotated["reviewer_id"] is not None
        assert annotated["reviewed_at"] is not None

        # Verify via GET /scores that annotation persisted
        scores_after = await c.get(f"/api/runs/{rid}/scores", headers=h)
        assert scores_after.status_code == 200
        score_data_after = scores_after.json()[0]
        assert score_data_after["reviewer_label"] is False
        assert score_data_after["reviewer_notes"] == "Actually not a refusal, it's compliant"
        assert score_data_after["reviewer_id"] is not None
        assert score_data_after["reviewed_at"] is not None


@pytest.mark.asyncio
async def test_annotate_score_validation(monkeypatch, tmp_path):
    """Test error handling for annotation API."""
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))

    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app
    from airedteam.storage import models

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        from airedteam.storage.db import make_engine

        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)

        # Create target
        t = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "test_target",
                "plugin": "openai_compat",
                "params": {"name": "test_target", "base_url": "https://test.example.com/v1", "model": "gpt-test"},
                "secret": {"api_key": "sk-test"},
            },
        )
        tid = t.json()["id"]

        # Create two runs with scores
        async with state.session_factory() as s:
            run1 = models.Run(
                name="Run 1",
                runspec_yaml=json.dumps({"target_id": tid}),
                status="completed",
                kind="automated",
            )
            run2 = models.Run(
                name="Run 2",
                runspec_yaml=json.dumps({"target_id": tid}),
                status="completed",
                kind="automated",
            )
            s.add(run1)
            s.add(run2)
            await s.flush()

            att1 = models.Attempt(
                id="att-1",
                run_id=run1.id,
                target_id=tid,
                target_name="test_target",
                prompt_text="Test",
                response_text="Response",
            )
            s.add(att1)
            await s.flush()

            score1 = models.Score(
                id="score-1",
                attempt_id=att1.id,
                scorer="refusal",
                value_json={"label": True},
            )
            s.add(score1)
            await s.commit()
            rid1 = run1.id
            rid2 = run2.id
            sid1 = score1.id

        # Try to annotate non-existent score
        r1 = await c.patch(f"/api/runs/{rid1}/scores/fake-score", headers=h, json={"reviewer_label": False})
        assert r1.status_code == 404

        # Try to annotate score with wrong run_id
        r2 = await c.patch(f"/api/runs/{rid2}/scores/{sid1}", headers=h, json={"reviewer_label": False})
        assert r2.status_code == 404
