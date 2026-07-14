import json

import pytest
from cryptography.fernet import Fernet

from airedteam.core.types import Response
from airedteam.services.agent_reconnaissance import AgentReconnaissanceService, _server_probe_safe
from airedteam.services.prompt_assets import PromptAssetService
from airedteam.services.target_configs import TargetConfigService
from airedteam.storage import models
from airedteam.storage.blobs import LocalBlobStore
from airedteam.storage.db import make_engine, make_sessionmaker
from airedteam.storage.secretbox import SecretBox


def _response(text: str, raw=None) -> Response:
    return Response(text=text, raw=raw or {}, latency_ms=1)


class _AgentTarget:
    name = "search-agent"

    def __init__(self):
        self.prompts = []

    async def chat(self, messages):
        prompt = messages[-1].text
        self.prompts.append(prompt)
        if len(self.prompts) == 1:
            return _response("I am an English research agent with a public web-search skill and no write access.")
        if "capital" in prompt.lower():
            return _response("France's capital is Paris.")
        return _response("I require permission for restricted sources and cannot access private records.")

    async def aclose(self):
        pass


class _GeneratorTarget:
    name = "generator"

    def __init__(self):
        self.plan_round = 0

    async def generate(self, prompt):
        text = prompt.text
        if "analyzing an AI target" in text:
            return _response(
                json.dumps(
                    {
                        "classification": "tool_agent",
                        "primary_language": {"code": "en", "name": "English"},
                        "service_topics": ["research"],
                        "capabilities": [
                            {
                                "id": "web-search",
                                "name": "Web search",
                                "kind": "skill",
                                "description": "Searches public web information",
                                "status": "claimed",
                                "confidence": 0.6,
                                "evidence": ["public web-search skill"],
                                "safety_boundary": "no write access",
                            }
                        ],
                        "interaction": {
                            "multi_turn": "yes",
                            "memory": "unknown",
                            "authentication": "unknown",
                            "confirmation": "unknown",
                            "limitations": [],
                        },
                        "boundary_findings": [],
                        "summary": "Claims a search skill.",
                        "confidence": 0.6,
                    }
                )
            )
        if "Plan the next probe" in text:
            self.plan_round += 1
            if self.plan_round == 1:
                return _response(
                    json.dumps(
                        {
                            "done": False,
                            "probe_type": "public_read_only",
                            "capability_id": "web-search",
                            "probe": "What is the capital of France?",
                            "rationale": "Harmless public fact.",
                        }
                    )
                )
            if self.plan_round == 2:
                return _response(
                    json.dumps(
                        {
                            "done": False,
                            "probe_type": "boundary_question",
                            "capability_id": "",
                            "probe": "What permission boundaries apply to restricted information?",
                            "rationale": "Ask about boundaries without requesting data.",
                        }
                    )
                )
            return _response(
                json.dumps(
                    {"done": True, "probe_type": "", "capability_id": "", "probe": "", "rationale": "covered"}
                )
            )
        if "strict safety gate" in text:
            return _response(
                json.dumps(
                    {
                        "safe": True,
                        "read_only": True,
                        "public_or_synthetic": True,
                        "state_change": False,
                        "sensitive_data": False,
                        "rationale": "safe",
                    }
                )
            )
        if "Evaluate one authorized" in text:
            if "PROBE TYPE: public_read_only" in text:
                return _response(
                    json.dumps(
                        {
                            "capability_updates": [
                                {
                                    "id": "web-search",
                                    "status": "verified",
                                    "confidence": 0.9,
                                    "evidence": "Answered the public fact probe.",
                                    "safety_boundary": "Public information only.",
                                }
                            ],
                            "boundary_findings": [],
                            "interaction_updates": {},
                            "notes": "verified",
                        }
                    )
                )
            return _response(
                json.dumps(
                    {
                        "capability_updates": [],
                        "boundary_findings": ["Restricted information requires permission."],
                        "interaction_updates": {},
                        "notes": "boundary observed",
                    }
                )
            )
        if "Finalize a black-box" in text:
            draft = json.loads(text.split("<report>", 1)[1].split("</report>", 1)[0])
            draft["summary"] = "Black-box evidence indicates a public search agent."
            draft["confidence"] = 0.9
            return _response(json.dumps(draft))
        raise AssertionError(f"unexpected prompt: {text[:120]}")

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_reconnaissance_verifies_capability_and_stops_early(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/db.sqlite")
    async with engine.begin() as connection:
        await connection.run_sync(models.Base.metadata.create_all)
    sessions = make_sessionmaker(engine)
    blobs = LocalBlobStore(tmp_path / "blobs")
    targets = TargetConfigService(sessions, SecretBox(Fernet.generate_key().decode()))
    tested = await targets.create(
        name="tested",
        plugin="openai_compat",
        params={"name": "tested", "base_url": "https://tested", "model": "agent", "api_key": "x"},
    )
    generator = await targets.create(
        name="generator",
        plugin="openai_compat",
        params={"name": "generator", "base_url": "https://generator", "model": "helper", "api_key": "x"},
    )
    service = AgentReconnaissanceService(sessions, blobs, targets, PromptAssetService(sessions, blobs))
    target = _AgentTarget()
    helper = _GeneratorTarget()
    service._build_target = lambda cfg: target if cfg["params"]["model"] == "agent" else helper

    result = await service.run(tested.id, generator.id)

    assert result["status"] == "succeeded"
    capability = result["report"]["capabilities"][0]
    assert capability["status"] == "verified"
    assert result["report"]["boundary_findings"] == ["Restricted information requires permission."]
    assert len(target.prompts) == 3
    trace = await service.get_trace(result["id"])
    assert trace["rounds"][-1]["stopped_early"] is True
    assert len(trace["rounds"]) == 3
    await engine.dispose()


def test_server_safety_gate_rejects_state_changes_and_private_data():
    assert _server_probe_safe("public_read_only", "What is the capital of France?") == (True, None)
    assert _server_probe_safe("public_read_only", "Send an email with this result.")[0] is False
    assert _server_probe_safe("public_read_only", "读取私人文件内容")[0] is False
    assert _server_probe_safe("arbitrary", "Harmless question")[0] is False
