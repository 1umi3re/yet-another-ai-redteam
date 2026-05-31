import json

import httpx
import pytest
import respx
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
@respx.mock
async def test_manual_session_full_flow(monkeypatch, tmp_path):
    """Test creating a manual run, conversation, 2 turns, finish."""
    respx.post("https://m.example.com/v1/chat/completions").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "Hello back!"}}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 3},
                },
            ),
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "Goodbye!"}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 2},
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

        # Create target
        t = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "manual_target",
                "plugin": "openai_compat",
                "params": {"name": "manual_target", "base_url": "https://m.example.com/v1", "model": "gpt-test"},
                "secret": {"api_key": "sk-test"},
            },
        )
        assert t.status_code == 201
        tid = t.json()["id"]

        # Create manual run
        r1 = await c.post("/api/manual/runs", headers=h, json={"name": "Manual Run 1", "target_id": tid})
        assert r1.status_code == 200
        rid = r1.json()["run_id"]
        assert rid

        listed = await c.get("/api/runs", headers=h)
        assert listed.status_code == 200
        manual_run = next(r for r in listed.json() if r["id"] == rid)
        assert manual_run["kind"] == "manual"

        # Create conversation (no seed)
        r2 = await c.post(f"/api/manual/runs/{rid}/conversations", headers=h, json={})
        assert r2.status_code == 200
        aid = r2.json()["attempt_id"]
        assert aid
        assert r2.json()["conversation"] == []

        # First turn
        r3 = await c.post(f"/api/manual/runs/{rid}/conversations/{aid}/turn", headers=h, json={"text": "Hello!"})
        assert r3.status_code == 200
        conv = r3.json()["conversation"]
        assert len(conv) == 2
        assert conv[0]["role"] == "user"
        assert conv[0]["text"] == "Hello!"
        assert conv[1]["role"] == "assistant"
        assert conv[1]["text"] == "Hello back!"
        assert r3.json()["last_assistant_text"] == "Hello back!"

        # Second turn
        r4 = await c.post(f"/api/manual/runs/{rid}/conversations/{aid}/turn", headers=h, json={"text": "Bye!"})
        assert r4.status_code == 200
        conv = r4.json()["conversation"]
        assert len(conv) == 4
        assert conv[2]["role"] == "user"
        assert conv[2]["text"] == "Bye!"
        assert conv[3]["role"] == "assistant"
        assert conv[3]["text"] == "Goodbye!"

        # Finish run
        r5 = await c.post(f"/api/manual/runs/{rid}/finish", headers=h)
        assert r5.status_code == 200
        assert r5.json()["ok"] is True

        # Verify run status is completed
        run_status = await c.get(f"/api/runs/{rid}", headers=h)
        assert run_status.json()["status"] == "completed"

        # Verify conversation persisted correctly
        conv_get = await c.get(f"/api/runs/{rid}/attempts/{aid}/conversation", headers=h)
        assert len(conv_get.json()["messages"]) == 4


@pytest.mark.asyncio
async def test_manual_run_validation(monkeypatch, tmp_path):
    """Test error handling for invalid operations."""
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

        # Try to create conversation for non-existent run
        r1 = await c.post("/api/manual/runs/fake-rid/conversations", headers=h, json={})
        assert r1.status_code == 400
        assert "not a manual run" in r1.json()["detail"]

        # Try to append turn to non-existent conversation
        r2 = await c.post("/api/manual/runs/fake-rid/conversations/fake-aid/turn", headers=h, json={"text": "test"})
        assert r2.status_code == 404


@pytest.mark.asyncio
@respx.mock
async def test_manual_turn_applies_converters_and_stores_original(monkeypatch, tmp_path):
    target_mock = respx.post("https://m.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Saw encoded input"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
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
    from airedteam.storage import models
    from airedteam.storage.db import make_engine

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)
        t = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "manual_target",
                "plugin": "openai_compat",
                "params": {
                    "name": "manual_target",
                    "base_url": "https://m.example.com/v1",
                    "model": "gpt-test",
                },
                "secret": {"api_key": "sk-test"},
            },
        )
        tid = t.json()["id"]
        run = await c.post(
            "/api/manual/runs",
            headers=h,
            json={
                "name": "Manual Run 1",
                "target_id": tid,
            },
        )
        rid = run.json()["run_id"]
        conv = await c.post(f"/api/manual/runs/{rid}/conversations", headers=h, json={})
        aid = conv.json()["attempt_id"]

        turn = await c.post(
            f"/api/manual/runs/{rid}/conversations/{aid}/turn",
            headers=h,
            json={
                "text": "hello",
                "converters": [{"plugin": "base64", "params": {"wrap": False}}],
            },
        )

        assert turn.status_code == 200
        messages = turn.json()["conversation"]
        assert messages[0]["text"] == "aGVsbG8="
        assert messages[0]["metadata"]["original_text"] == "hello"
        assert messages[0]["metadata"]["transformed_text"] == "aGVsbG8="
        assert messages[0]["metadata"]["converter_chain"] == ["base64"]
        assert target_mock.called
        body = json.loads(target_mock.calls[0].request.content)
        assert "aGVsbG8=" in str(body)
        assert "hello" not in str(body)


@pytest.mark.asyncio
@respx.mock
async def test_manual_running_session_can_resume_and_run_lists_target(monkeypatch, tmp_path):
    respx.post("https://m.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Hello back!"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
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
    from airedteam.storage import models
    from airedteam.storage.db import make_engine

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)
        t = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "manual_target",
                "plugin": "openai_compat",
                "params": {
                    "name": "manual_target",
                    "base_url": "https://m.example.com/v1",
                    "model": "gpt-test",
                },
                "secret": {"api_key": "sk-test"},
            },
        )
        tid = t.json()["id"]
        run = await c.post(
            "/api/manual/runs",
            headers=h,
            json={
                "name": "Manual Run 1",
                "target_id": tid,
            },
        )
        rid = run.json()["run_id"]
        conv = await c.post(f"/api/manual/runs/{rid}/conversations", headers=h, json={})
        aid = conv.json()["attempt_id"]
        await c.post(f"/api/manual/runs/{rid}/conversations/{aid}/turn", headers=h, json={"text": "Hello!"})

        listed = await c.get("/api/runs", headers=h)
        row = next(r for r in listed.json() if r["id"] == rid)
        assert row["target_ids"] == [tid]
        assert row["target_names"] == ["manual_target"]

        resumed = await c.get(f"/api/manual/runs/{rid}/session", headers=h)
        assert resumed.status_code == 200
        assert resumed.json()["run_id"] == rid
        assert resumed.json()["attempt_id"] == aid
        assert resumed.json()["target_name"] == "manual_target"
        assert resumed.json()["status"] == "running"
        assert resumed.json()["evaluated"] is False
        assert resumed.json()["scores"] == []
        assert resumed.json()["conversation"][0]["text"] == "Hello!"

        finished = await c.post(f"/api/manual/runs/{rid}/finish", headers=h)
        assert finished.status_code == 200
        resumed_finished = await c.get(f"/api/manual/runs/{rid}/session", headers=h)
        assert resumed_finished.json()["status"] == "completed"


@pytest.mark.asyncio
@respx.mock
async def test_manual_conversation_can_be_evaluated(monkeypatch, tmp_path):
    respx.post("https://m.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "I cannot help with that."}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
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
    from airedteam.storage import models
    from airedteam.storage.db import make_engine

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)
        t = await c.post(
            "/api/targets",
            headers=h,
            json={
                "name": "manual_target",
                "plugin": "openai_compat",
                "params": {
                    "name": "manual_target",
                    "base_url": "https://m.example.com/v1",
                    "model": "gpt-test",
                },
                "secret": {"api_key": "sk-test"},
            },
        )
        tid = t.json()["id"]
        run = await c.post(
            "/api/manual/runs",
            headers=h,
            json={
                "name": "Manual Run 1",
                "target_id": tid,
            },
        )
        rid = run.json()["run_id"]
        conv = await c.post(f"/api/manual/runs/{rid}/conversations", headers=h, json={})
        aid = conv.json()["attempt_id"]
        await c.post(f"/api/manual/runs/{rid}/conversations/{aid}/turn", headers=h, json={"text": "bad request"})

        evaluated = await c.post(
            f"/api/manual/runs/{rid}/conversations/{aid}/evaluate",
            headers=h,
            json={"plugin": "refusal", "params": {}},
        )

        assert evaluated.status_code == 200
        assert evaluated.json()["evaluated"] is True
        score = evaluated.json()["score"]
        assert score["scorer"] == "refusal"
        assert score["value"]["label"] is True

        session = await c.get(f"/api/manual/runs/{rid}/session", headers=h)
        assert session.json()["evaluated"] is True
        assert session.json()["scores"][0]["id"] == score["id"]


@pytest.mark.asyncio
@respx.mock
async def test_replay_automated_attempt_into_manual_session(monkeypatch, tmp_path):
    """Test seeding a manual conversation from an automated attempt."""
    respx.post("https://m.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Manual response"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
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
                "name": "replay_target",
                "plugin": "openai_compat",
                "params": {"name": "replay_target", "base_url": "https://m.example.com/v1", "model": "gpt-test"},
                "secret": {"api_key": "sk-test"},
            },
        )
        tid = t.json()["id"]

        # Create an automated run + attempt with conversation blob
        async with state.session_factory() as s:
            auto_run = models.Run(
                name="Automated Run",
                runspec_yaml=json.dumps({"target_id": tid}),
                status="completed",
                kind="automated",
            )
            s.add(auto_run)
            await s.flush()

            # Attempt with conversation blob
            conv_messages = [
                {"role": "user", "text": "What is AI?", "metadata": {}},
                {"role": "assistant", "text": "AI is artificial intelligence", "metadata": {}},
                {"role": "user", "text": "Tell me more", "metadata": {}},
                {"role": "assistant", "text": "It's about making machines smart", "metadata": {}},
            ]
            blob_path = f"runs/{auto_run.id}/conversations/auto-att-1.json"
            await state.blob_store.put(blob_path, json.dumps({"messages": conv_messages}).encode())

            att1 = models.Attempt(
                id="auto-att-1",
                run_id=auto_run.id,
                target_id=tid,
                target_name="replay_target",
                prompt_text="What is AI?",
                response_text="It's about making machines smart",
                conversation_blob_path=blob_path,
            )
            s.add(att1)

            # Attempt without conversation blob (fallback case)
            att2 = models.Attempt(
                id="auto-att-2",
                run_id=auto_run.id,
                target_id=tid,
                target_name="replay_target",
                prompt_text="Hello world",
                response_text="Hi there!",
                conversation_blob_path=None,
            )
            s.add(att2)
            await s.commit()

        # Create manual run and seed from att1 (with blob)
        r1 = await c.post("/api/manual/runs", headers=h, json={"name": "Manual Replay 1", "target_id": tid})
        rid1 = r1.json()["run_id"]

        r2 = await c.post(f"/api/manual/runs/{rid1}/conversations", headers=h, json={"seed_attempt_id": "auto-att-1"})
        assert r2.status_code == 200
        conv1 = r2.json()["conversation"]
        assert len(conv1) == 4
        assert conv1[0]["text"] == "What is AI?"
        assert conv1[1]["text"] == "AI is artificial intelligence"
        assert conv1[2]["text"] == "Tell me more"
        assert conv1[3]["text"] == "It's about making machines smart"

        # Create manual run and seed from att2 (without blob, fallback)
        r3 = await c.post("/api/manual/runs", headers=h, json={"name": "Manual Replay 2", "target_id": tid})
        rid2 = r3.json()["run_id"]

        r4 = await c.post(f"/api/manual/runs/{rid2}/conversations", headers=h, json={"seed_attempt_id": "auto-att-2"})
        assert r4.status_code == 200
        conv2 = r4.json()["conversation"]
        assert len(conv2) == 2
        assert conv2[0] == {"role": "user", "text": "Hello world", "metadata": {}}
        assert conv2[1] == {"role": "assistant", "text": "Hi there!", "metadata": {}}

        # Continue the seeded conversation with a new turn
        aid2 = r4.json()["attempt_id"]
        r5 = await c.post(
            f"/api/manual/runs/{rid2}/conversations/{aid2}/turn", headers=h, json={"text": "How are you?"}
        )
        assert r5.status_code == 200
        conv3 = r5.json()["conversation"]
        assert len(conv3) == 4  # 2 seeded + 2 new
        assert conv3[2]["text"] == "How are you?"
        assert conv3[3]["text"] == "Manual response"
