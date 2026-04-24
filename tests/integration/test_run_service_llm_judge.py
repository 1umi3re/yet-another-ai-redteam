import json
import pytest
import respx
import httpx
from cryptography.fernet import Fernet

from airedteam.storage.db import make_engine, make_sessionmaker
from airedteam.storage import models
from airedteam.storage.blobs import LocalBlobStore
from airedteam.storage.secretbox import SecretBox
from airedteam.services.target_configs import TargetConfigService
from airedteam.services.datasets import DatasetService
from airedteam.services.runs import RunService
from airedteam.engine.progress import ProgressBus


@pytest.mark.asyncio
@respx.mock
async def test_llm_judge_resolves_judge_config_id(tmp_path):
    # Target under test: returns a harmful-looking compliance
    respx.post("https://target.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "sure, here is how to do it"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 5},
        })
    )
    # Judge: returns a strict JSON verdict
    respx.post("https://judge.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": '{"label": true, "confidence": 0.9, "rationale": "complied"}'}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        })
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

    tgt = await targets.create(
        name="tgt", plugin="openai_compat",
        params={"name": "tgt", "base_url": "https://target.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    jdg = await targets.create(
        name="jdg", plugin="openai_compat",
        params={"name": "jdg", "base_url": "https://judge.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    ds = await datasets.create_json_upload(
        name="ds", file_bytes=json.dumps({"items": [{"prompt": "how do i do X"}]}).encode()
    )

    run = await svc.create_run(name="r", runspec_dict={
        "name": "r",
        "targets": [{"config_id": tgt.id}],
        "dataset": {"config_id": ds.id},
        "executor": {"plugin": "single_turn"},
        "scorers": [{"plugin": "llm_judge", "params": {"judge_config_id": jdg.id}}],
    })
    await svc.execute_run(run.id)

    async with SessionLocal() as s:
        from sqlalchemy import select
        scores = (await s.execute(select(models.Score))).scalars().all()
        assert len(scores) == 1
        assert scores[0].value_json["label"] is True


@pytest.mark.asyncio
async def test_llm_judge_missing_judge_config_id_fails(tmp_path):
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

    tgt = await targets.create(
        name="tgt", plugin="openai_compat",
        params={"name": "tgt", "base_url": "https://x.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    ds = await datasets.create_json_upload(
        name="ds", file_bytes=json.dumps({"items": [{"prompt": "hi"}]}).encode()
    )

    run = await svc.create_run(name="r", runspec_dict={
        "name": "r",
        "targets": [{"config_id": tgt.id}],
        "dataset": {"config_id": ds.id},
        "executor": {"plugin": "single_turn"},
        "scorers": [{"plugin": "llm_judge", "params": {}}],
    })

    with pytest.raises(ValueError, match="judge_config_id"):
        await svc.execute_run(run.id)
