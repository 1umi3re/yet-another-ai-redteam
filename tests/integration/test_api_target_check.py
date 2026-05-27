import asyncio
import pytest
import respx
import httpx
from cryptography.fernet import Fernet
from httpx import AsyncClient, ASGITransport
from airedteam.core.registry import default_registry
from airedteam.core.types import Response


async def _login(c):
    r = await c.post("/api/login", json={"password": "letmein"})
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.mark.asyncio
@respx.mock
async def test_target_check_success(monkeypatch, tmp_path):
    """Test successful target connectivity check."""
    respx.post("https://check.example.com/v1/chat/completions").mock(
        side_effect=[
            httpx.Response(200, json={
                "choices": [{"message": {"content": "pong - all systems operational"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 4}
            }),
            httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                content=(
                    b'data: {"choices":[{"delta":{"content":"p"}}]}\n\n'
                    b'data: [DONE]\n\n'
                ),
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
        from airedteam.storage.db import make_engine
        from airedteam.storage import models
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        
        h = await _login(c)
        
        # Create target
        t = await c.post("/api/targets", headers=h, json={
            "name": "check_target",
            "plugin": "openai_compat",
            "params": {
                "name": "check_target",
                "base_url": "https://check.example.com/v1",
                "model": "gpt-test"
            },
            "secret": {"api_key": "sk-test"}
        })
        assert t.status_code == 201
        tid = t.json()["id"]
        
        # Check the target
        check_resp = await c.post(f"/api/targets/{tid}/check", headers=h)
        assert check_resp.status_code == 200
        
        result = check_resp.json()
        assert result["ok"] is True
        assert isinstance(result["latency_ms"], int)
        assert result["latency_ms"] >= 0
        assert result["response_preview"] is not None
        assert "pong" in result["response_preview"]
        assert result["stream_ok"] is True
        assert result["stream_error"] is None
        assert result["error"] is None
        assert result["model_echo"] == "gpt-test"


@pytest.mark.asyncio
@respx.mock
async def test_target_check_failure(monkeypatch, tmp_path):
    """Test target check when endpoint returns error."""
    respx.post("https://bad.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(401, json={"error": "Invalid API key"})
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
        from airedteam.storage.db import make_engine
        from airedteam.storage import models
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        
        h = await _login(c)
        
        # Create target with bad credentials
        t = await c.post("/api/targets", headers=h, json={
            "name": "bad_target",
            "plugin": "openai_compat",
            "params": {
                "name": "bad_target",
                "base_url": "https://bad.example.com/v1",
                "model": "gpt-test"
            },
            "secret": {"api_key": "sk-invalid"}
        })
        assert t.status_code == 201
        tid = t.json()["id"]
        
        # Check should return ok=false with error details
        check_resp = await c.post(f"/api/targets/{tid}/check", headers=h)
        assert check_resp.status_code == 200
        
        result = check_resp.json()
        assert result["ok"] is False
        assert result["error"] is not None
        assert len(result["error"]) > 0
        assert result["latency_ms"] is None
        assert result["response_preview"] is None


@pytest.mark.asyncio
@respx.mock
async def test_target_check_draft(monkeypatch, tmp_path):
    """Test checking a target config without saving it."""
    respx.post("https://draft.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "pong from draft"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3}
        })
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
        from airedteam.storage.db import make_engine
        from airedteam.storage import models
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        
        h = await _login(c)
        
        # Check draft target without saving
        check_resp = await c.post("/api/targets/check", headers=h, json={
            "name": "draft_target",
            "plugin": "openai_compat",
            "params": {
                "name": "draft_target",
                "base_url": "https://draft.example.com/v1",
                "model": "gpt-draft"
            },
            "secret": {"api_key": "sk-draft"}
        })
        assert check_resp.status_code == 200
        
        result = check_resp.json()
        assert result["ok"] is True
        assert isinstance(result["latency_ms"], int)
        assert "pong from draft" in result["response_preview"]
        
        # Verify target was not persisted
        targets = await c.get("/api/targets", headers=h)
        assert len(targets.json()) == 0


@pytest.mark.asyncio
async def test_target_check_draft_uses_configured_timeout(monkeypatch, tmp_path):
    class SlowCheckTarget:
        def __init__(self, *, name: str, timeout: float) -> None:
            self.name = name
            self.timeout = timeout

        async def generate(self, prompt):
            await asyncio.sleep(0.05)
            return Response(text="late pong", raw={}, latency_ms=50)

        async def aclose(self):
            pass

    default_registry().register("targets", "slow_check_target", SlowCheckTarget)
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
        from airedteam.storage.db import make_engine
        from airedteam.storage import models
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)

        h = await _login(c)

        check_resp = await c.post("/api/targets/check", headers=h, json={
            "name": "slow_target",
            "plugin": "slow_check_target",
            "params": {"name": "slow_target", "timeout": 0.01},
        })
        assert check_resp.status_code == 200
        result = check_resp.json()
        assert result["ok"] is False
        assert result["error"] == "TimeoutError: Request exceeded 0.01 seconds"


@pytest.mark.asyncio
async def test_target_check_not_found(monkeypatch, tmp_path):
    """Test checking a non-existent target returns 404."""
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
        from airedteam.storage.db import make_engine
        from airedteam.storage import models
        eng = make_engine(state.settings.database_url)
        async with eng.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        
        h = await _login(c)
        
        # Check non-existent target
        check_resp = await c.post("/api/targets/fake-id/check", headers=h)
        assert check_resp.status_code == 404
