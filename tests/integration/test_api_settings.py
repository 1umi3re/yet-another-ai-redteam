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
async def test_monitoring_settings_api_updates_and_sends_test(monkeypatch, tmp_path):
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=test"
    route = respx.post(webhook).mock(return_value=httpx.Response(200, json={"errcode": 0}))
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/x.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    import airedteam.api.deps as deps

    deps._STATE = None
    from airedteam.api.app import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        h = await _login(c)
        initial = (await c.get("/api/settings/monitoring", headers=h)).json()
        assert initial["monitor_enabled"] is True
        assert initial["dingtalk_webhook_configured"] is False

        updated = await c.patch(
            "/api/settings/monitoring",
            headers=h,
            json={
                "monitor_enabled": True,
                "dingtalk_webhook_url": webhook,
                "monitor_failure_rate_threshold": 0.3,
                "monitor_empty_response_rate_threshold": 0.15,
                "monitor_score_failure_rate_threshold": 0.25,
                "monitor_min_samples": 5,
                "monitor_no_progress_seconds": 60,
                "monitor_alert_cooldown_seconds": 120,
            },
        )
        assert updated.status_code == 200
        body = updated.json()
        assert body["delivery_enabled"] is True
        assert body["dingtalk_webhook_configured"] is True
        assert "access_token=%2A%2A%2A" in body["dingtalk_webhook_url_display"]
        assert body["monitor_failure_rate_threshold"] == 0.3

        sent = await c.post("/api/settings/monitoring/test", headers=h)
        assert sent.status_code == 200
        assert sent.json() == {"sent": True}
        assert route.called
        payload = json.loads(route.calls[0].request.content.decode("utf-8"))
        assert payload["msgtype"] == "markdown"
