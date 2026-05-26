import json

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


async def _setup_app(monkeypatch, tmp_path):
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
    return app, state, models


@pytest.mark.asyncio
async def test_run_report_export_and_filters(monkeypatch, tmp_path):
    app, state, models = await _setup_app(monkeypatch, tmp_path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        h = await _login(c)
        async with state.session_factory() as s:
            run = models.Run(
                name="report-run",
                runspec_yaml=json.dumps({"targets": []}),
                status="completed",
            )
            s.add(run)
            await s.flush()
            a1 = models.Attempt(
                id="a1",
                run_id=run.id,
                target_id="target-1",
                target_name="Target 1",
                dataset_item_id="item-1",
                prompt_text="p1",
                response_text="I cannot help",
                converter_chain=["base64"],
                latency_ms=10,
                tokens_in=2,
                tokens_out=3,
            )
            a2 = models.Attempt(
                id="a2",
                run_id=run.id,
                target_id="target-1",
                target_name="Target 1",
                dataset_item_id="item-2",
                prompt_text="p2",
                response_text="answer",
                converter_chain=[],
                latency_ms=20,
                tokens_in=4,
                tokens_out=5,
            )
            s.add_all([a1, a2])
            await s.flush()
            s.add_all([
                models.Score(
                    id="s1",
                    attempt_id="a1",
                    scorer="refusal",
                    value_json={"label": True},
                    rationale="refused",
                ),
                models.Score(
                    id="s2",
                    attempt_id="a2",
                    scorer="llm_judge",
                    value_json={"label": False},
                    rationale="judge said refused",
                    reviewer_label=False,
                    reviewer_notes="actually complied",
                ),
            ])
            await s.commit()
            run_id = run.id

        report = (await c.get(f"/api/runs/{run_id}/report", headers=h)).json()
        assert report["totals"]["attempts"] == 2
        assert report["totals"]["refused"] == 1
        assert report["totals"]["complied"] == 1
        by_scorer = {row["scorer"]: row for row in report["by_scorer"]}
        assert by_scorer["llm_judge"]["reviewer_overrides"] == 1

        attempts_default = (await c.get(f"/api/runs/{run_id}/attempts", headers=h)).json()
        assert isinstance(attempts_default, list)
        attempts_page = (await c.get(
            f"/api/runs/{run_id}/attempts?paged=true&verdict=complied",
            headers=h,
        )).json()
        assert attempts_page["total"] == 1
        assert attempts_page["items"][0]["id"] == "a2"

        reviewed_scores = (await c.get(
            f"/api/runs/{run_id}/scores?paged=true&reviewed=true",
            headers=h,
        )).json()
        assert reviewed_scores["total"] == 1
        assert reviewed_scores["items"][0]["id"] == "s2"

        exported = (await c.get(f"/api/runs/{run_id}/export?format=json", headers=h)).json()
        assert exported["attempts"][1]["final_verdict"] == "complied"
        csv_resp = await c.get(f"/api/runs/{run_id}/export?format=csv", headers=h)
        assert csv_resp.status_code == 200
        assert "attempt_id" in csv_resp.text
        assert "a1" in csv_resp.text


@pytest.mark.asyncio
async def test_cancel_pending_run(monkeypatch, tmp_path):
    app, state, models = await _setup_app(monkeypatch, tmp_path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        h = await _login(c)
        async with state.session_factory() as s:
            run = models.Run(name="cancel-me", runspec_yaml=json.dumps({}), status="pending")
            s.add(run)
            await s.commit()
            run_id = run.id

        resp = await c.post(f"/api/runs/{run_id}/cancel", headers=h)
        assert resp.status_code == 202
        got = (await c.get(f"/api/runs/{run_id}", headers=h)).json()
        assert got["status"] == "cancelled"
