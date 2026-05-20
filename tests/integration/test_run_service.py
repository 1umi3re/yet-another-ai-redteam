import json, pytest
from cryptography.fernet import Fernet
from airedteam.storage.db import make_engine, make_sessionmaker
from airedteam.storage import models
from airedteam.storage.blobs import LocalBlobStore
from airedteam.storage.secretbox import SecretBox
from airedteam.services.target_configs import TargetConfigService
from airedteam.services.datasets import DatasetService
from airedteam.services.runs import RunService
from airedteam.engine.progress import ProgressBus
import respx, httpx


@pytest.mark.asyncio
@respx.mock
async def test_run_end_to_end(tmp_path):
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "I cannot help with that"}}],
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
    svc = RunService(SessionLocal, blob, box, targets, datasets, bus, response_inline_max_bytes=8192, max_concurrency=2)

    tcfg = await targets.create(name="t1", plugin="openai_compat",
                                params={"name": "t1", "base_url": "https://api.example.com/v1", "model": "m"},
                                secret={"api_key": "sk"})
    ds = await datasets.create_json_upload(name="ds", file_bytes=json.dumps({"items": [{"prompt": "hi"}]}).encode())

    run = await svc.create_run(name="r1", runspec_dict={
        "name": "r1",
        "targets": [{"config_id": tcfg.id}],
        "dataset": {"config_id": ds.id},
        "executor": {"plugin": "single_turn"},
        "scorers": [{"plugin": "refusal"}],
    })
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
async def test_run_service_executes_best_of_n(tmp_path):
    route = respx.post("https://api.example.com/v1/chat/completions").mock(
        side_effect=[
            httpx.Response(200, json={
                "choices": [{"message": {"content": "I cannot help with that."}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            }),
            httpx.Response(200, json={
                "choices": [{"message": {"content": "candidate with direct useful content"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            }),
            httpx.Response(200, json={
                "choices": [{"message": {"content": "short"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            }),
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

    tcfg = await targets.create(name="t1", plugin="openai_compat",
                                params={"name": "t1", "base_url": "https://api.example.com/v1", "model": "m"},
                                secret={"api_key": "sk"})
    ds = await datasets.create_json_upload(name="ds", file_bytes=json.dumps({"items": [{"prompt": "hi"}]}).encode())

    run = await svc.create_run(name="r1", runspec_dict={
        "name": "r1",
        "targets": [{"config_id": tcfg.id}],
        "dataset": {"config_id": ds.id},
        "executor": {"plugin": "best_of_n", "params": {"attempts": 3, "seed": 2}},
    })
    await svc.execute_run(run.id)

    async with SessionLocal() as s:
        from sqlalchemy import select
        attempt = (await s.execute(select(models.Attempt).where(models.Attempt.run_id == run.id))).scalar_one()
        assert attempt.response_text == "candidate with direct useful content"
        assert attempt.prompt_text != "hi"
        assert attempt.status == "completed"
    assert route.call_count == 3
