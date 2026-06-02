import asyncio
import json

import httpx
import pytest
import respx
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient

from airedteam.core.registry import default_registry
from airedteam.core.types import Response


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
@respx.mock
async def test_create_and_run_via_api(monkeypatch, tmp_path):
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "I cannot help"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
    )
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        # Ensure tables exist
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
            files={"file": ("a.json", json.dumps({"items": [{"prompt": "hi"}]}).encode(), "application/json")},
            data={"name": "d1"},
        )
        did = ds.json()["id"]
        cr = await c.post(
            "/api/runs",
            headers=h,
            json={
                "name": "r1",
                "runspec": {
                    "name": "r1",
                    "targets": [{"config_id": tid}],
                    "dataset": {"config_id": did},
                    "executor": {"plugin": "single_turn"},
                    "scorers": [{"plugin": "refusal"}],
                },
            },
        )
        assert cr.status_code == 201
        assert cr.json()["kind"] == "automated"
        rid = cr.json()["id"]
        st = await c.post(f"/api/runs/{rid}/start", headers=h)
        assert st.status_code == 202
        for _ in range(50):
            s = (await c.get(f"/api/runs/{rid}", headers=h)).json()
            if s["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.05)
        assert s["status"] == "completed"
        assert s["kind"] == "automated"
        attempts = (await c.get(f"/api/runs/{rid}/attempts", headers=h)).json()
        assert len(attempts) == 1
        assert attempts[0]["run_id"] == rid
        scores = (await c.get(f"/api/runs/{rid}/scores", headers=h)).json()
        assert scores[0]["value"]["label"] is True


@pytest.mark.asyncio
@respx.mock
async def test_attempts_api_returns_original_transformed_prompt_and_response(monkeypatch, tmp_path):
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "model response"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2},
            },
        )
    )
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        from airedteam.storage import models
        from airedteam.storage.db import make_engine

        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)
        target = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "t1",
                "plugin": "openai_compat",
                "params": {"name": "t1", "base_url": "https://api.example.com/v1", "model": "m"},
                "secret": {"api_key": "sk"},
            },
        )
        dataset = await c.post(
            "/api/datasets/upload",
            headers=h,
            files={"file": ("a.json", json.dumps({"items": [{"prompt": "hi"}]}).encode(), "application/json")},
            data={"name": "d1"},
        )
        run = await c.post(
            "/api/runs",
            headers=h,
            json={
                "name": "r1",
                "runspec": {
                    "name": "r1",
                    "targets": [{"config_id": target.json()["id"]}],
                    "dataset": {"config_id": dataset.json()["id"]},
                    "converters": [{"plugin": "base64", "params": {"wrap": False}}],
                    "executor": {"plugin": "single_turn"},
                    "scorers": [{"plugin": "refusal"}],
                },
            },
        )
        rid = run.json()["id"]
        assert (await c.post(f"/api/runs/{rid}/start", headers=h)).status_code == 202
        for _ in range(50):
            status = (await c.get(f"/api/runs/{rid}", headers=h)).json()
            if status["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.05)

        assert status["status"] == "completed"
        attempts = (await c.get(f"/api/runs/{rid}/attempts", headers=h)).json()
        assert attempts[0]["original_prompt"] == "hi"
        assert attempts[0]["transformed_prompt"] == "aGk="
        assert attempts[0]["prompt"] == "aGk="
        assert attempts[0]["response"] == "model response"


@pytest.mark.asyncio
@respx.mock
async def test_retry_failed_llm_judge_scores_via_api(monkeypatch, tmp_path):
    respx.post("https://target.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "target complied"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2},
            },
        )
    )
    judge_route = respx.post("https://judge.example.com/v1/chat/completions").mock(
        side_effect=[
            httpx.Response(500, json={"error": {"message": "judge unavailable"}}),
            httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": '{"label": true, "confidence": 0.9, "rationale": "complied"}'
                            }
                        }
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
        ]
    )
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        from airedteam.storage import models
        from airedteam.storage.db import make_engine

        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)
        target = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "target",
                "plugin": "openai_compat",
                "params": {"name": "target", "base_url": "https://target.example.com/v1", "model": "m"},
                "secret": {"api_key": "sk"},
            },
        )
        judge = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "judge",
                "plugin": "openai_compat",
                "params": {"name": "judge", "base_url": "https://judge.example.com/v1", "model": "m"},
                "secret": {"api_key": "sk"},
            },
        )
        ds = await c.post(
            "/api/datasets/upload",
            headers=h,
            files={"file": ("a.json", json.dumps({"items": [{"prompt": "hi"}]}).encode(), "application/json")},
            data={"name": "d1"},
        )
        cr = await c.post(
            "/api/runs",
            headers=h,
            json={
                "name": "r1",
                "runspec": {
                    "name": "r1",
                    "targets": [{"config_id": target.json()["id"]}],
                    "dataset": {"config_id": ds.json()["id"]},
                    "executor": {"plugin": "single_turn"},
                    "scorers": [{"plugin": "llm_judge", "params": {"judge_config_id": judge.json()["id"]}}],
                },
            },
        )
        rid = cr.json()["id"]

        assert (await c.post(f"/api/runs/{rid}/start", headers=h)).status_code == 202
        for _ in range(50):
            status = (await c.get(f"/api/runs/{rid}", headers=h)).json()
            if status["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.05)

        assert status["status"] == "completed"
        scores = (await c.get(f"/api/runs/{rid}/scores", headers=h)).json()
        assert len(scores) == 1
        assert scores[0]["status"] == "failed"
        assert scores[0]["retryable"] is True
        assert scores[0]["value"]["status"] == "failed"
        assert "judge unavailable" in scores[0]["value"]["error"]

        retry = await c.post(f"/api/runs/{rid}/scores/retry", headers=h, json={"failed_only": True})
        assert retry.status_code == 202
        assert retry.json()["retried"] == 1
        assert retry.json()["failed"] == 0
        assert judge_route.call_count == 2

        scores = (await c.get(f"/api/runs/{rid}/scores", headers=h)).json()
        assert len(scores) == 1
        assert scores[0]["status"] == "completed"
        assert scores[0]["retryable"] is False
        assert scores[0]["value"]["label"] is True
        assert scores[0]["final_verdict"] == "complied"


@pytest.mark.asyncio
async def test_pause_and_resume_run_via_api(monkeypatch, tmp_path):
    started = asyncio.Event()
    release = asyncio.Event()
    calls: list[str] = []

    class BlockingApiTarget:
        def __init__(self, *, name: str) -> None:
            self.name = name

        async def generate(self, prompt):
            calls.append(prompt.text)
            if len(calls) == 1:
                started.set()
                await release.wait()
            return Response(text=f"ok:{prompt.text}", raw={}, latency_ms=1)

        async def aclose(self):
            pass

    default_registry().register("targets", "blocking_api_pause_target", BlockingApiTarget)

    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app

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
            json={"name": "t1", "plugin": "blocking_api_pause_target", "params": {"name": "t1"}},
        )
        tid = t.json()["id"]
        ds = await c.post(
            "/api/datasets/upload",
            headers=h,
            files={
                "file": (
                    "a.json",
                    json.dumps({"items": [{"prompt": "a"}, {"prompt": "b"}]}).encode(),
                    "application/json",
                )
            },
            data={"name": "d1"},
        )
        did = ds.json()["id"]
        cr = await c.post(
            "/api/runs",
            headers=h,
            json={
                "name": "r1",
                "runspec": {
                    "name": "r1",
                    "targets": [{"config_id": tid}],
                    "dataset": {"config_id": did},
                    "executor": {"plugin": "single_turn"},
                    "concurrency": 1,
                },
            },
        )
        rid = cr.json()["id"]
        assert (await c.post(f"/api/runs/{rid}/start", headers=h)).status_code == 202
        await asyncio.wait_for(started.wait(), timeout=1)
        pause = await c.post(f"/api/runs/{rid}/pause", headers=h)
        assert pause.status_code == 202
        release.set()

        for _ in range(50):
            status = (await c.get(f"/api/runs/{rid}", headers=h)).json()
            if status["status"] == "paused":
                break
            await asyncio.sleep(0.02)
        assert status["status"] == "paused"
        assert status["progress_done"] == 1
        assert status["progress_total"] == 2

        resume = await c.post(f"/api/runs/{rid}/resume", headers=h, json={"retry_failed": False})
        assert resume.status_code == 202
        for _ in range(50):
            status = (await c.get(f"/api/runs/{rid}", headers=h)).json()
            if status["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.02)

        assert status["status"] == "completed"
        attempts = (await c.get(f"/api/runs/{rid}/attempts", headers=h)).json()
        assert [a["prompt"] for a in attempts] == ["a", "b"]


@pytest.mark.asyncio
@respx.mock
async def test_get_conversation_multi_turn_api(monkeypatch, tmp_path):
    from airedteam.builtins.executors.multi_turn_base import MultiTurnExecutor
    from airedteam.core.registry import default_registry
    from airedteam.core.types import Message

    class EchoMultiTurnAPI(MultiTurnExecutor):
        name = "multi_turn_echo_api_test"
        max_turns = 2

        async def next_user_message(self, state, last_response):
            return Message(role="user", text="again please")

        async def should_stop(self, state, last_response):
            return state["turn"] >= self.max_turns

    default_registry().register("executors", "multi_turn_echo_api_test", EchoMultiTurnAPI)

    respx.post("https://api.example.com/v1/chat/completions").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "first-reply"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "second-reply"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
        ]
    )
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app

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
            files={"file": ("a.json", json.dumps({"items": [{"prompt": "hi"}]}).encode(), "application/json")},
            data={"name": "d1"},
        )
        did = ds.json()["id"]
        cr = await c.post(
            "/api/runs",
            headers=h,
            json={
                "name": "r1",
                "runspec": {
                    "name": "r1",
                    "targets": [{"config_id": tid}],
                    "dataset": {"config_id": did},
                    "executor": {"plugin": "multi_turn_echo_api_test"},
                    "scorers": [{"plugin": "refusal"}],
                },
            },
        )
        rid = cr.json()["id"]
        await c.post(f"/api/runs/{rid}/start", headers=h)
        for _ in range(50):
            s = (await c.get(f"/api/runs/{rid}", headers=h)).json()
            if s["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.05)
        assert s["status"] == "completed"
        attempts = (await c.get(f"/api/runs/{rid}/attempts", headers=h)).json()
        assert attempts[0]["run_id"] == rid
        aid = attempts[0]["id"]

        conv = await c.get(f"/api/runs/{rid}/attempts/{aid}/conversation", headers=h)
        assert conv.status_code == 200
        payload = conv.json()
        assert [m["role"] for m in payload["messages"]] == ["user", "assistant", "user", "assistant"]
        assert payload["messages"][-1]["text"] == "second-reply"
