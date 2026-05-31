import asyncio
import json

import httpx
import pytest
import respx
from cryptography.fernet import Fernet

from airedteam.core.registry import default_registry
from airedteam.core.types import Response
from airedteam.engine.progress import ProgressBus
from airedteam.services.datasets import DatasetService
from airedteam.services.runs import RunService
from airedteam.services.target_configs import TargetConfigService
from airedteam.storage import models
from airedteam.storage.blobs import LocalBlobStore
from airedteam.storage.db import make_engine, make_sessionmaker
from airedteam.storage.secretbox import SecretBox


@pytest.mark.asyncio
@respx.mock
async def test_run_end_to_end(tmp_path):
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "I cannot help with that"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
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
            "executor": {"plugin": "single_turn"},
            "scorers": [{"plugin": "refusal"}],
        },
    )
    await svc.execute_run(run.id)

    async with SessionLocal() as s:
        from sqlalchemy import select

        attempts = (await s.execute(select(models.Attempt).where(models.Attempt.run_id == run.id))).scalars().all()
        assert len(attempts) == 1
        scores = (await s.execute(select(models.Score))).scalars().all()
        assert scores[0].value_json["label"] is True
        run_row = await s.get(models.Run, run.id)
        assert run_row.status == "completed"
        assert run_row.progress_done == 1


@pytest.mark.asyncio
@respx.mock
async def test_run_service_runs_selected_converters_as_independent_attempts(tmp_path):
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "target-response"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
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
            "converters": [
                {"plugin": "base64", "params": {"wrap": False}},
                {"plugin": "leetspeak"},
            ],
            "executor": {"plugin": "single_turn"},
        },
    )
    await svc.execute_run(run.id)

    async with SessionLocal() as s:
        from sqlalchemy import select

        attempts = (await s.execute(select(models.Attempt).where(models.Attempt.run_id == run.id))).scalars().all()
        assert len(attempts) == 2
        assert sorted(a.converter_chain for a in attempts) == [["base64"], ["leetspeak"]]
        assert sorted(a.prompt_text for a in attempts) == ["aGk=", "h1"]
        run_row = await s.get(models.Run, run.id)
        assert run_row.status == "completed"
        assert run_row.progress_done == 2
        assert run_row.progress_total == 2


@pytest.mark.asyncio
async def test_run_service_applies_target_max_concurrency(tmp_path):
    class SlowTarget:
        active = 0
        max_seen = 0

        def __init__(self, *, name: str) -> None:
            self.name = name

        async def generate(self, prompt):
            type(self).active += 1
            type(self).max_seen = max(type(self).max_seen, type(self).active)
            try:
                await asyncio.sleep(0.01)
                return Response(text="ok", raw={}, latency_ms=1)
            finally:
                type(self).active -= 1

        async def aclose(self):
            pass

    SlowTarget.active = 0
    SlowTarget.max_seen = 0
    default_registry().register("targets", "slow_target", SlowTarget)

    engine_db = make_engine(f"sqlite+aiosqlite:///{tmp_path}/x.db")
    SessionLocal = make_sessionmaker(engine_db)
    async with engine_db.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    blob = LocalBlobStore(tmp_path / "blobs")
    box = SecretBox(Fernet.generate_key().decode())
    targets = TargetConfigService(SessionLocal, box)
    datasets = DatasetService(SessionLocal, blob)
    bus = ProgressBus()
    svc = RunService(SessionLocal, blob, box, targets, datasets, bus, max_concurrency=3)

    tcfg = await targets.create(
        name="t1",
        plugin="slow_target",
        params={"name": "t1", "max_concurrency": "1"},
    )
    ds = await datasets.create_json_upload(
        name="ds",
        file_bytes=json.dumps({"items": [{"prompt": "a"}, {"prompt": "b"}, {"prompt": "c"}]}).encode(),
    )

    run = await svc.create_run(
        name="r1",
        runspec_dict={
            "name": "r1",
            "targets": [{"config_id": tcfg.id}],
            "dataset": {"config_id": ds.id},
            "executor": {"plugin": "single_turn"},
            "concurrency": 3,
        },
    )
    await svc.execute_run(run.id)

    async with SessionLocal() as s:
        from sqlalchemy import select

        attempts = (await s.execute(select(models.Attempt).where(models.Attempt.run_id == run.id))).scalars().all()
        assert len(attempts) == 3
    assert SlowTarget.max_seen == 1


@pytest.mark.asyncio
@respx.mock
async def test_run_service_executes_best_of_n(tmp_path):
    route = respx.post("https://api.example.com/v1/chat/completions").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "I cannot help with that."}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "candidate with direct useful content"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "short"}}],
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
            "executor": {"plugin": "best_of_n", "params": {"attempts": 3, "seed": 2}},
        },
    )
    await svc.execute_run(run.id)

    async with SessionLocal() as s:
        from sqlalchemy import select

        attempt = (await s.execute(select(models.Attempt).where(models.Attempt.run_id == run.id))).scalar_one()
        assert attempt.response_text == "candidate with direct useful content"
        assert attempt.prompt_text != "hi"
        assert attempt.status == "completed"
    assert route.call_count == 3


@pytest.mark.asyncio
@respx.mock
async def test_run_service_resolves_attack_template_asset_for_template_jailbreak(tmp_path):
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "target-response"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
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
    ds = await datasets.create_json_upload(
        name="ds", file_bytes=json.dumps({"items": [{"prompt": "objective"}]}).encode()
    )

    run = await svc.create_run(
        name="r1",
        runspec_dict={
            "name": "r1",
            "targets": [{"config_id": tcfg.id}],
            "dataset": {"config_id": ds.id},
            "converters": [
                {
                    "plugin": "template_jailbreak",
                    "params": {"attack_template_asset_id": "attack_template.controlled_safety_test.v1"},
                }
            ],
            "executor": {"plugin": "single_turn"},
        },
    )
    await svc.execute_run(run.id)

    async with SessionLocal() as s:
        from sqlalchemy import select

        attempt = (await s.execute(select(models.Attempt).where(models.Attempt.run_id == run.id))).scalar_one()
        assert "Controlled safety test objective:" in attempt.prompt_text
        assert "objective" in attempt.prompt_text
        assert attempt.response_text == "target-response"


@pytest.mark.asyncio
async def test_run_service_marks_setup_failure_failed(tmp_path):
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
            "executor": {"plugin": "general_multi_turn", "params": {}},
        },
    )

    with pytest.raises(ValueError):
        await svc.execute_run(run.id)

    async with SessionLocal() as s:
        run_row = await s.get(models.Run, run.id)
        assert run_row.status == "failed"
        assert "attacker_config_id" in run_row.error
