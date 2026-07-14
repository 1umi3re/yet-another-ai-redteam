import json

import pytest
from cryptography.fernet import Fernet
from httpx import ASGITransport, AsyncClient

from airedteam.core.registry import default_registry
from airedteam.core.types import Response


class _ReconApiTarget:
    def __init__(self, *, name: str, model: str):
        self.name = name
        self.model = model

    async def chat(self, messages):
        if self.model == "agent":
            if len(messages) == 1:
                return Response(text="I am a research agent with no write access.", raw={}, latency_ms=1)
            return Response(text="I only use public sources.", raw={}, latency_ms=1)
        return await self.generate(type("Prompt", (), {"text": messages[-1].text})())

    async def generate(self, prompt):
        text = prompt.text
        if "analyzing an AI target" in text:
            return Response(
                text=json.dumps(
                    {
                        "classification": "service_agent",
                        "primary_language": {"code": "en", "name": "English"},
                        "service_topics": ["research"],
                        "capabilities": [],
                        "interaction": {
                            "multi_turn": "yes",
                            "memory": "unknown",
                            "authentication": "unknown",
                            "confirmation": "unknown",
                            "limitations": [],
                        },
                        "boundary_findings": [],
                        "summary": "Research agent.",
                        "confidence": 0.7,
                    }
                ),
                raw={},
                latency_ms=1,
            )
        if "Plan the next probe" in text:
            payload = {
                "done": False,
                "probe_type": "boundary_question",
                "capability_id": "",
                "probe": "What permission boundaries apply to restricted information?",
                "rationale": "Boundary inventory.",
            }
        elif "strict safety gate" in text:
            payload = {
                "safe": True,
                "read_only": True,
                "public_or_synthetic": True,
                "state_change": False,
                "sensitive_data": False,
                "rationale": "safe",
            }
        elif "Evaluate one authorized" in text:
            payload = {
                "capability_updates": [],
                "boundary_findings": ["Public sources only."],
                "interaction_updates": {},
                "notes": "boundary observed",
            }
        elif "Finalize a black-box" in text:
            payload = json.loads(text.split("<report>", 1)[1].split("</report>", 1)[0])
            payload["summary"] = "Black-box research-agent report."
        else:
            raise AssertionError(f"unexpected helper prompt: {text[:100]}")
        return Response(text=json.dumps(payload), raw={}, latency_ms=1)

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_reconnaissance_api_runs_lists_and_returns_trace(monkeypatch, tmp_path):
    default_registry().register("targets", "recon_api_target", _ReconApiTarget)
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/api.db")
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

        async def create_target(name, model):
            response = await client.post(
                "/api/targets",
                headers=headers,
                json={"name": name, "plugin": "recon_api_target", "params": {"name": name, "model": model}},
            )
            return response.json()

        tested = await create_target("tested", "agent")
        generator = await create_target("generator", "helper")
        run = await client.post(
            f"/api/targets/{tested['id']}/reconnaissance/run",
            headers=headers,
            json={"generator_config_id": generator["id"], "max_rounds": 1},
        )
        assert run.status_code == 200, run.text
        report = run.json()
        assert report["status"] == "succeeded"
        assert report["report"]["classification"] == "service_agent"
        assert report["report"]["boundary_findings"] == ["Public sources only."]

        listed = await client.get(f"/api/targets/{tested['id']}/reconnaissance", headers=headers)
        assert [item["id"] for item in listed.json()] == [report["id"]]
        trace = await client.get(
            f"/api/targets/{tested['id']}/reconnaissance/{report['id']}/trace",
            headers=headers,
        )
        assert trace.status_code == 200
        assert trace.json()["rounds"][0]["probe_type"] == "boundary_question"

        same_target = await client.post(
            f"/api/targets/{tested['id']}/reconnaissance/run",
            headers=headers,
            json={"generator_config_id": tested["id"], "max_rounds": 1},
        )
        assert same_target.status_code == 400
