import csv
import io
import json
from datetime import datetime, timedelta

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
                started_at=datetime(2026, 1, 1, 0, 0, 0),
                finished_at=datetime(2026, 1, 1, 0, 0, 2),
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
                executor_name="base64",
                executor_kind="converter_method",
                dataset_item_language="en",
                started_at=datetime(2026, 1, 1, 0, 0, 0),
                finished_at=datetime(2026, 1, 1, 0, 0, 0, 100000),
                duration_ms=100,
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
                conversation_blob_path=f"runs/{run.id}/conversations/a2.json",
                converter_chain=[],
                executor_name="single_turn",
                executor_kind="executor",
                dataset_item_language="zh",
                started_at=datetime(2026, 1, 1, 0, 0, 0, 200000),
                finished_at=datetime(2026, 1, 1, 0, 0, 0, 500000),
                duration_ms=300,
                latency_ms=20,
                tokens_in=4,
                tokens_out=5,
            )
            a3 = models.Attempt(
                id="a3",
                run_id=run.id,
                target_id="target-2",
                target_name="Target 2",
                dataset_item_id="item-3",
                prompt_text="p3",
                response_text="answer",
                converter_chain=["base64"],
                executor_name="base64",
                executor_kind="converter_method",
                dataset_item_language="en",
                started_at=datetime(2026, 1, 1, 0, 0, 0, 600000),
                finished_at=datetime(2026, 1, 1, 0, 0, 1),
                duration_ms=400,
                latency_ms=30,
                tokens_in=6,
                tokens_out=7,
            )
            a4 = models.Attempt(
                id="a4",
                run_id=run.id,
                target_id="target-2",
                target_name="Target 2",
                dataset_item_id="item-4",
                prompt_text="p4",
                response_text=None,
                converter_chain=[],
                executor_name="single_turn",
                executor_kind="executor",
                dataset_item_language="zh",
                status="failed",
                started_at=datetime(2026, 1, 1, 0, 0, 1, 100000),
                finished_at=datetime(2026, 1, 1, 0, 0, 1, 300000),
                duration_ms=200,
                latency_ms=40,
                tokens_in=8,
                tokens_out=9,
            )
            s.add_all([a1, a2, a3, a4])
            await s.flush()
            conversation_messages = [
                {"role": "user", "text": "first transformed prompt", "metadata": {"turn": 1}},
                {"role": "assistant", "text": "first response", "metadata": {}},
                {"role": "user", "text": "follow-up prompt", "metadata": {"turn": 2}},
                {"role": "assistant", "text": "final response", "metadata": {"final": True}},
            ]
            await state.blob_store.put(
                a2.conversation_blob_path,
                json.dumps({"messages": conversation_messages}).encode("utf-8"),
            )
            s.add_all(
                [
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
                    models.Score(
                        id="s3",
                        attempt_id="a3",
                        scorer="llm_judge",
                        value_json={"label": True},
                        rationale="judge said complied",
                    ),
                ]
            )
            await s.commit()
            run_id = run.id

        report = (await c.get(f"/api/runs/{run_id}/report", headers=h)).json()
        assert report["run"]["started_at"] == "2026-01-01T00:00:00"
        assert report["run"]["finished_at"] == "2026-01-01T00:00:02"
        assert report["run"]["duration_ms"] == 2000
        assert report["totals"]["attempts"] == 4
        assert report["totals"]["duration_ms"] == 1000
        assert report["totals"]["refused"] == 1
        assert report["totals"]["complied"] == 2
        assert report["totals"]["failed"] == 1
        by_scorer = {row["scorer"]: row for row in report["by_scorer"]}
        assert by_scorer["llm_judge"]["reviewer_overrides"] == 1
        by_target_chain = {
            (row["target_id"], tuple(row["converter_chain"])): row for row in report["by_target_chain"]
        }
        assert by_target_chain[("target-1", ("base64",))]["success_rate"] == 0
        assert by_target_chain[("target-1", ())]["success_rate"] == 1
        assert by_target_chain[("target-2", ("base64",))]["success_rate"] == 1
        assert by_target_chain[("target-2", ())]["failed"] == 1
        assert by_target_chain[("target-2", ())]["unscored"] == 1
        assert by_target_chain[("target-2", ())]["success_rate"] is None
        by_executor = {row["executor_name"]: row for row in report["by_executor"]}
        assert by_executor["base64"]["attempts"] == 2
        assert by_executor["base64"]["complied"] == 1
        assert by_executor["single_turn"]["attempts"] == 2
        by_target_executor = {
            (row["target_id"], row["executor_name"]): row for row in report["by_target_executor"]
        }
        assert by_target_executor[("target-1", "base64")]["success_rate"] == 0
        assert by_target_executor[("target-2", "single_turn")]["failed"] == 1

        attempts_default = (await c.get(f"/api/runs/{run_id}/attempts", headers=h)).json()
        assert isinstance(attempts_default, list)
        assert attempts_default[0]["started_at"] == "2026-01-01T00:00:00"
        assert attempts_default[0]["finished_at"] == "2026-01-01T00:00:00.100000"
        assert attempts_default[0]["duration_ms"] == 100
        attempts_page = (
            await c.get(
                f"/api/runs/{run_id}/attempts?paged=true&verdict=complied",
                headers=h,
            )
        ).json()
        assert attempts_page["total"] == 2
        assert {item["id"] for item in attempts_page["items"]} == {"a2", "a3"}
        converter_attempts = (
            await c.get(
                f"/api/runs/{run_id}/attempts?paged=true&converter=base64",
                headers=h,
            )
        ).json()
        assert converter_attempts["total"] == 2
        assert {item["id"] for item in converter_attempts["items"]} == {"a1", "a3"}
        no_converter_attempts = (
            await c.get(
                f"/api/runs/{run_id}/attempts?paged=true&converter=(none)",
                headers=h,
            )
        ).json()
        assert no_converter_attempts["total"] == 2
        assert {item["id"] for item in no_converter_attempts["items"]} == {"a2", "a4"}
        executor_attempts = (
            await c.get(
                f"/api/runs/{run_id}/attempts?paged=true&executor=base64",
                headers=h,
            )
        ).json()
        assert executor_attempts["total"] == 2
        assert {item["id"] for item in executor_attempts["items"]} == {"a1", "a3"}
        assert executor_attempts["items"][0]["executor_name"] == "base64"

        reviewed_scores = (
            await c.get(
                f"/api/runs/{run_id}/scores?paged=true&reviewed=true",
                headers=h,
            )
        ).json()
        assert reviewed_scores["total"] == 1
        assert reviewed_scores["items"][0]["id"] == "s2"

        exported = (await c.get(f"/api/runs/{run_id}/export?format=json", headers=h)).json()
        assert exported["run"]["duration_ms"] == 2000
        assert exported["attempts"][0]["duration_ms"] == 100
        assert exported["attempts"][1]["final_verdict"] == "complied"
        assert exported["attempts"][0]["executor_name"] == "base64"
        assert exported["attempts"][0]["dataset_item_language"] == "en"
        exported_by_id = {attempt["id"]: attempt for attempt in exported["attempts"]}
        assert exported_by_id["a1"]["messages"] == []
        assert exported_by_id["a2"]["messages"] == conversation_messages
        filtered_export = (
            await c.get(
                f"/api/runs/{run_id}/export?format=json&verdict=complied&target_id=target-1&executor=single_turn",
                headers=h,
            )
        ).json()
        assert [attempt["id"] for attempt in filtered_export["attempts"]] == ["a2"]
        assert filtered_export["attempts"][0]["scores"][0]["id"] == "s2"
        assert filtered_export["attempts"][0]["messages"] == conversation_messages
        status_export = (
            await c.get(
                f"/api/runs/{run_id}/export?format=json&status=failed",
                headers=h,
            )
        ).json()
        assert [attempt["id"] for attempt in status_export["attempts"]] == ["a4"]
        filtered_csv_resp = await c.get(
            f"/api/runs/{run_id}/export?format=csv&verdict=complied&target_id=target-1&executor=single_turn",
            headers=h,
        )
        assert filtered_csv_resp.status_code == 200
        filtered_csv_rows = list(csv.DictReader(io.StringIO(filtered_csv_resp.text)))
        assert [row["attempt_id"] for row in filtered_csv_rows] == ["a2"]
        assert json.loads(filtered_csv_rows[0]["messages"]) == conversation_messages
        csv_resp = await c.get(f"/api/runs/{run_id}/export?format=csv", headers=h)
        assert csv_resp.status_code == 200
        assert "attempt_id" in csv_resp.text
        assert "executor_name" in csv_resp.text
        assert "duration_ms" in csv_resp.text
        assert "messages" in csv_resp.text
        assert "a1" in csv_resp.text


@pytest.mark.asyncio
async def test_run_html_report_export_is_readable_escaped_and_sampled(monkeypatch, tmp_path):
    app, state, models = await _setup_app(monkeypatch, tmp_path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        h = await _login(c)
        async with state.session_factory() as s:
            run = models.Run(
                name="html-report-run",
                runspec_yaml=json.dumps({"targets": []}),
                status="completed",
                started_at=datetime(2026, 1, 1, 0, 0, 0),
                finished_at=datetime(2026, 1, 1, 0, 0, 3),
            )
            s.add(run)
            await s.flush()
            run_id = run.id
            base_time = datetime(2026, 1, 1, 0, 0, 0)
            attempts = []
            scores = []

            def add_attempt(
                attempt_id: str,
                *,
                target_id: str,
                target_name: str,
                executor_name: str,
                prompt: str,
                response: str | None = "model response",
                status: str = "completed",
                verdict: str | None = "complied",
            ) -> None:
                offset = len(attempts)
                attempt = models.Attempt(
                    id=attempt_id,
                    run_id=run_id,
                    target_id=target_id,
                    target_name=target_name,
                    dataset_item_id=f"item-{attempt_id}",
                    original_prompt_text=f"original {prompt}",
                    prompt_text=prompt,
                    response_text=response,
                    converter_chain=[executor_name],
                    executor_name=executor_name,
                    executor_kind="converter_method",
                    status=status,
                    started_at=base_time + timedelta(milliseconds=offset * 10),
                    finished_at=base_time + timedelta(milliseconds=offset * 10 + 5),
                    duration_ms=5,
                )
                attempts.append(attempt)
                if verdict is not None:
                    scores.append(
                        models.Score(
                            id=f"score-{attempt_id}",
                            attempt_id=attempt_id,
                            scorer="llm_judge",
                            value_json={"attack_success": verdict == "complied"},
                            rationale=f"{verdict} rationale",
                        )
                    )

            for i in range(4):
                add_attempt(
                    f"success-a-{i}",
                    target_id="target-a",
                    target_name="Target A",
                    executor_name="method-a",
                    prompt=f"sample-combo-a-{i + 1} <script>alert('x')</script>",
                    response="Use <b>bold</b> & raw",
                )
            for i in range(9):
                add_attempt(
                    f"success-extra-{i}",
                    target_id=f"target-extra-{i}",
                    target_name=f"Target Extra {i}",
                    executor_name=f"method-extra-{i}",
                    prompt=f"top-combo-{i}",
                )
            add_attempt(
                "low-risk",
                target_id="target-low",
                target_name="Target Low",
                executor_name="method-low",
                prompt="low-risk-combo",
                verdict="refused",
            )
            for i in range(12):
                add_attempt(
                    f"attention-{i}",
                    target_id="target-attention",
                    target_name="Target Attention",
                    executor_name="method-attention",
                    prompt=f"attention-record-{i:02d}",
                    response=None,
                    status="failed" if i % 2 == 0 else "completed",
                    verdict=None,
                )

            s.add_all(attempts + scores)
            await s.commit()

        resp = await c.get(f"/api/runs/{run_id}/report.html?lang=zh", headers=h)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/html")
        assert f"run-{run_id}-report.html" in resp.headers["content-disposition"]
        body = resp.text
        assert "自动化测试报告" in body
        assert "html-report-run" in body
        assert "攻击成功率" in body
        assert "代表性样例" in body
        assert "需关注记录" in body
        assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in body
        assert "<script>alert" not in body
        assert "Use &lt;b&gt;bold&lt;/b&gt; &amp; raw" in body
        assert "sample-combo-a-1" in body
        assert "sample-combo-a-2" in body
        assert "sample-combo-a-3" in body
        assert "sample-combo-a-4" not in body
        assert "attention-record-09" in body
        assert "attention-record-10" not in body
        assert "low-risk-combo" not in body

        en_resp = await c.get(f"/api/runs/{run_id}/report.html?lang=en", headers=h)
        assert en_resp.status_code == 200
        assert "Automated Test Report" in en_resp.text
        assert "Representative Samples" in en_resp.text


@pytest.mark.asyncio
async def test_run_html_report_export_rejects_manual_runs(monkeypatch, tmp_path):
    app, state, models = await _setup_app(monkeypatch, tmp_path)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        h = await _login(c)
        async with state.session_factory() as s:
            run = models.Run(
                name="manual-report-run",
                kind="manual",
                runspec_yaml=json.dumps({"target_id": "target-1"}),
                status="completed",
            )
            s.add(run)
            await s.commit()
            run_id = run.id

        resp = await c.get(f"/api/runs/{run_id}/report.html", headers=h)
        assert resp.status_code == 400
        assert "automated" in resp.json()["detail"]


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
