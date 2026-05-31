from __future__ import annotations

import json

import httpx
import pytest
import respx
from cryptography.fernet import Fernet

from airedteam.builtins.executors.multi_turn_base import MultiTurnExecutor
from airedteam.core.registry import default_registry
from airedteam.core.types import Message
from airedteam.engine.progress import ProgressBus
from airedteam.services.datasets import DatasetService
from airedteam.services.runs import RunService
from airedteam.services.target_configs import TargetConfigService
from airedteam.storage import models
from airedteam.storage.blobs import LocalBlobStore
from airedteam.storage.db import make_engine, make_sessionmaker
from airedteam.storage.secretbox import SecretBox


class EchoMultiTurn(MultiTurnExecutor):
    """Test-only 2-turn executor: seed then a fixed follow-up."""

    name = "multi_turn_echo_test"
    max_turns = 2

    async def next_user_message(self, state, last_response):
        return Message(role="user", text="again please")

    async def should_stop(self, state, last_response):
        return state["turn"] >= self.max_turns


@pytest.fixture(autouse=True)
def _register_echo_executor():
    default_registry().register("executors", "multi_turn_echo_test", EchoMultiTurn)
    yield


@pytest.mark.asyncio
@respx.mock
async def test_multi_turn_attempt_writes_conversation_blob(tmp_path):
    # two sequential /chat/completions responses
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
    engine_db = make_engine(f"sqlite+aiosqlite:///{tmp_path}/x.db")
    SessionLocal = make_sessionmaker(engine_db)
    async with engine_db.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    blob = LocalBlobStore(tmp_path / "blobs")
    box = SecretBox(Fernet.generate_key().decode())
    targets = TargetConfigService(SessionLocal, box)
    datasets = DatasetService(SessionLocal, blob)
    bus = ProgressBus()
    svc = RunService(SessionLocal, blob, box, targets, datasets, bus, response_inline_max_bytes=8192, max_concurrency=2)

    tcfg = await targets.create(
        name="t1",
        plugin="openai_compat",
        params={"name": "t1", "base_url": "https://api.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    ds = await datasets.create_json_upload(name="ds", file_bytes=json.dumps({"items": [{"prompt": "hi"}]}).encode())

    run = await svc.create_run(
        name="r1",
        runspec_dict={
            "name": "r1",
            "targets": [{"config_id": tcfg.id}],
            "dataset": {"config_id": ds.id},
            "executor": {"plugin": "multi_turn_echo_test"},
            "scorers": [{"plugin": "refusal"}],
        },
    )
    await svc.execute_run(run.id)

    from sqlalchemy import select

    async with SessionLocal() as s:
        attempts = (await s.execute(select(models.Attempt).where(models.Attempt.run_id == run.id))).scalars().all()
        assert len(attempts) == 1
        a = attempts[0]
        assert a.conversation_blob_path is not None
        assert a.response_text == "second-reply"

    raw = await blob.get(a.conversation_blob_path)
    payload = json.loads(raw.decode("utf-8"))
    assert [m["role"] for m in payload["messages"]] == ["user", "assistant", "user", "assistant"]
    assert payload["messages"][-1]["text"] == "second-reply"


@pytest.mark.asyncio
@respx.mock
async def test_multi_turn_conversation_blob_includes_artifacts(tmp_path):
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
    engine_db = make_engine(f"sqlite+aiosqlite:///{tmp_path}/x.db")
    SessionLocal = make_sessionmaker(engine_db)
    async with engine_db.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    blob = LocalBlobStore(tmp_path / "blobs")
    box = SecretBox(Fernet.generate_key().decode())
    targets = TargetConfigService(SessionLocal, box)
    datasets = DatasetService(SessionLocal, blob)
    bus = ProgressBus()
    svc = RunService(SessionLocal, blob, box, targets, datasets, bus)

    tcfg = await targets.create(
        name="t1",
        plugin="openai_compat",
        params={"name": "t1", "base_url": "https://api.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    ds = await datasets.create_json_upload(name="ds", file_bytes=json.dumps({"items": [{"prompt": "hi"}]}).encode())

    run = await svc.create_run(
        name="r1",
        runspec_dict={
            "name": "r1",
            "targets": [{"config_id": tcfg.id}],
            "dataset": {"config_id": ds.id},
            "converters": [
                {
                    "plugin": "add_text_image",
                    "params": {"output_dir": str(tmp_path / "artifacts")},
                }
            ],
            "executor": {"plugin": "multi_turn_echo_test"},
        },
    )
    await svc.execute_run(run.id)

    from sqlalchemy import select

    async with SessionLocal() as s:
        attempt = (await s.execute(select(models.Attempt).where(models.Attempt.run_id == run.id))).scalar_one()

    raw = await blob.get(attempt.conversation_blob_path)
    payload = json.loads(raw.decode("utf-8"))
    first = payload["messages"][0]
    assert first["artifacts"][0]["kind"] == "image"
    assert first["artifacts"][0]["media_type"] == "image/svg+xml"
    assert first["artifacts"][0]["path"].endswith(".svg")
