import pytest, json, asyncio, respx, httpx
from cryptography.fernet import Fernet
from httpx import AsyncClient, ASGITransport


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
@respx.mock
async def test_create_and_run_via_api(monkeypatch, tmp_path):
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices":[{"message":{"content":"I cannot help"}}], "usage":{"prompt_tokens":1,"completion_tokens":1}}))
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps; deps._STATE = None
    from airedteam.api.app import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        # Ensure tables exist
        state = deps.get_state()
        from airedteam.storage.db import make_engine
        from airedteam.storage import models
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        
        h = await _login(c)
        t = await c.post("/api/targets", headers=h, json={
            "name": "t1", "plugin": "openai_compat",
            "params": {"name":"t1","base_url":"https://api.example.com/v1","model":"m"},
            "secret": {"api_key":"sk"}})
        tid = t.json()["id"]
        ds = await c.post("/api/datasets/upload", headers=h,
                           files={"file":("a.json", json.dumps({"items":[{"prompt":"hi"}]}).encode(), "application/json")},
                           data={"name":"d1"})
        did = ds.json()["id"]
        cr = await c.post("/api/runs", headers=h, json={
            "name":"r1",
            "runspec": {
                "name":"r1",
                "targets":[{"config_id": tid}],
                "dataset":{"config_id": did},
                "executor":{"plugin":"single_turn"},
                "scorers":[{"plugin":"refusal"}],
            }})
        assert cr.status_code == 201
        rid = cr.json()["id"]
        st = await c.post(f"/api/runs/{rid}/start", headers=h)
        assert st.status_code == 202
        for _ in range(50):
            s = (await c.get(f"/api/runs/{rid}", headers=h)).json()
            if s["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.05)
        assert s["status"] == "completed"
        attempts = (await c.get(f"/api/runs/{rid}/attempts", headers=h)).json()
        assert len(attempts) == 1
        scores = (await c.get(f"/api/runs/{rid}/scores", headers=h)).json()
        assert scores[0]["value"]["label"] is True


@pytest.mark.asyncio
@respx.mock
async def test_get_conversation_multi_turn_api(monkeypatch, tmp_path):
    from airedteam.core.registry import default_registry
    from airedteam.core.types import Message
    from airedteam.builtins.executors.multi_turn_base import MultiTurnExecutor
    
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
            httpx.Response(200, json={"choices":[{"message":{"content":"first-reply"}}], "usage":{"prompt_tokens":1,"completion_tokens":1}}),
            httpx.Response(200, json={"choices":[{"message":{"content":"second-reply"}}], "usage":{"prompt_tokens":1,"completion_tokens":1}}),
        ]
    )
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps; deps._STATE = None
    from airedteam.api.app import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        state = deps.get_state()
        from airedteam.storage.db import make_engine
        from airedteam.storage import models
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        
        h = await _login(c)
        t = await c.post("/api/targets", headers=h, json={
            "name": "t1", "plugin": "openai_compat",
            "params": {"name":"t1","base_url":"https://api.example.com/v1","model":"m"},
            "secret": {"api_key":"sk"}})
        tid = t.json()["id"]
        ds = await c.post("/api/datasets/upload", headers=h,
                           files={"file":("a.json", json.dumps({"items":[{"prompt":"hi"}]}).encode(), "application/json")},
                           data={"name":"d1"})
        did = ds.json()["id"]
        cr = await c.post("/api/runs", headers=h, json={
            "name":"r1",
            "runspec": {
                "name":"r1",
                "targets":[{"config_id": tid}],
                "dataset":{"config_id": did},
                "executor":{"plugin":"multi_turn_echo_api_test"},
                "scorers":[{"plugin":"refusal"}],
            }})
        rid = cr.json()["id"]
        await c.post(f"/api/runs/{rid}/start", headers=h)
        for _ in range(50):
            s = (await c.get(f"/api/runs/{rid}", headers=h)).json()
            if s["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.05)
        assert s["status"] == "completed"
        attempts = (await c.get(f"/api/runs/{rid}/attempts", headers=h)).json()
        aid = attempts[0]["id"]
        
        conv = await c.get(f"/api/runs/{rid}/attempts/{aid}/conversation", headers=h)
        assert conv.status_code == 200
        payload = conv.json()
        assert [m["role"] for m in payload["messages"]] == ["user", "assistant", "user", "assistant"]
        assert payload["messages"][-1]["text"] == "second-reply"
