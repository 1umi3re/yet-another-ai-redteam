import asyncio
import json

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient

from airedteam.core.registry import default_registry
from airedteam.core.types import Response


async def _wait_for_run(client, headers, run_id):
    for _ in range(100):
        result = (await client.get(f"/api/runs/{run_id}", headers=headers)).json()
        if result["status"] in {"completed", "failed"}:
            return result
        await asyncio.sleep(0.02)
    raise AssertionError("run did not finish")


@pytest.mark.asyncio
async def test_successful_attempts_can_be_exactly_replayed_or_reapplied(monkeypatch, tmp_path):
    calls: list[str] = []

    class RecordingTarget:
        def __init__(self, *, name: str, model: str):
            self.name = name

        async def generate(self, prompt):
            calls.append(prompt.text)
            return Response(text=f"answered:{prompt.text}", raw={}, latency_ms=1)

        async def aclose(self):
            pass

    default_registry().register("targets", "retest_recording_target", RecordingTarget)
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        state = deps.get_state()
        engine = make_engine(state.settings.database_url)
        async with engine.begin() as connection:
            await connection.run_sync(models.Base.metadata.create_all)
        token = (await client.post("/api/login", json={"password": "letmein"})).json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        target = (
            await client.post(
                "/api/targets",
                headers=headers,
                json={
                    "name": "target",
                    "plugin": "retest_recording_target",
                    "params": {"name": "target", "model": "m"},
                },
            )
        ).json()
        async with state.session_factory() as session:
            session.add(
                models.ServiceContextTemplate(
                    target_config_id=target["id"],
                    target_model="m",
                    generator_model="generator",
                    version=1,
                    status="succeeded",
                    is_active=True,
                    template_text="TOPIC:{prompt}",
                    verification_passed=True,
                )
            )
            await session.commit()
        dataset = (
            await client.post(
                "/api/datasets/upload",
                headers=headers,
                files={"file": ("items.json", json.dumps({"items": [{"prompt": "hello"}]}), "application/json")},
                data={"name": "source"},
            )
        ).json()
        source = (
            await client.post(
                "/api/runs",
                headers=headers,
                json={
                    "name": "source run",
                    "runspec": {
                        "version": 2,
                        "name": "source run",
                        "targets": [{"config_id": target["id"]}],
                        "dataset": {"config_id": dataset["id"]},
                        "executors": [{"kind": "executor", "plugin": "single_turn"}],
                        "scorers": [{"plugin": "refusal"}],
                    },
                },
            )
        ).json()
        await client.post(f"/api/runs/{source['id']}/start", headers=headers)
        assert (await _wait_for_run(client, headers, source["id"]))["status"] == "completed"

        preview = (
            await client.get(f"/api/targets/{target['id']}/successful-attempts", headers=headers)
        ).json()
        assert preview["total"] == 1
        assert preview["summary"]["reapply_available"] == 1
        assert preview["items"][0]["provenance_quality"] == "exact"
        source_attempt_id = preview["items"][0]["id"]

        for mode in ("exact_replay", "reapply_method"):
            created = await client.post(
                "/api/retests",
                headers=headers,
                json={
                    "name": mode,
                    "target_config_id": target["id"],
                    "mode": mode,
                    "scorer": {"plugin": "refusal", "params": {}},
                    "select_all": False,
                    "attempt_ids": [source_attempt_id],
                },
            )
            assert created.status_code == 201, created.text
            run = created.json()
            assert run["subtype"] == "retest"
            await client.post(f"/api/runs/{run['id']}/start", headers=headers)
            assert (await _wait_for_run(client, headers, run["id"]))["status"] == "completed"
            attempts = (await client.get(f"/api/runs/{run['id']}/attempts", headers=headers)).json()
            assert len(attempts) == 1
            assert attempts[0]["source_attempt_id"] == source_attempt_id
            assert attempts[0]["source_run_id"] == source["id"]
            assert attempts[0]["retest_mode"] == mode

        # Source and method-reapply use the active bridge. Exact replay sends the
        # already bridged prompt directly, so it must not become TOPIC:TOPIC:hello.
        assert calls == ["TOPIC:hello", "TOPIC:hello", "TOPIC:hello"]
