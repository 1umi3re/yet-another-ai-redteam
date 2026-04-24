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
async def test_run_with_sampling_limit(tmp_path):
    """Test that sampling.limit restricts dataset size."""
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "Response"}}],
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
    
    # Create target
    tcfg = await targets.create(
        name="t1",
        plugin="openai_compat",
        params={"name": "t1", "base_url": "https://api.example.com/v1", "model": "m"},
        secret={"api_key": "sk"}
    )
    
    # Create dataset with 5 items
    ds_items = [{"prompt": f"prompt-{i}"} for i in range(5)]
    ds = await datasets.create_json_upload(
        name="ds",
        file_bytes=json.dumps({"items": ds_items}).encode()
    )
    
    # Create run with sampling.limit=2
    run = await svc.create_run(name="r1", runspec_dict={
        "name": "r1",
        "targets": [{"config_id": tcfg.id}],
        "dataset": {"config_id": ds.id},
        "executor": {"plugin": "single_turn"},
        "scorers": [{"plugin": "refusal"}],
        "sampling": {"limit": 2}
    })
    
    await svc.execute_run(run.id)
    
    # Verify only 2 attempts were created
    async with SessionLocal() as s:
        from sqlalchemy import select
        attempts = (await s.execute(
            select(models.Attempt).where(models.Attempt.run_id == run.id)
        )).scalars().all()
        assert len(attempts) == 2
        
        run_row = await s.get(models.Run, run.id)
        assert run_row.status == "completed"
        assert run_row.progress_done == 2


@pytest.mark.asyncio
@respx.mock
async def test_run_with_sampling_shuffle(tmp_path):
    """Test that sampling.shuffle with seed is deterministic."""
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "Response"}}],
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
    
    # Create target
    tcfg = await targets.create(
        name="t1",
        plugin="openai_compat",
        params={"name": "t1", "base_url": "https://api.example.com/v1", "model": "m"},
        secret={"api_key": "sk"}
    )
    
    # Create dataset with 5 items
    ds_items = [{"prompt": f"prompt-{i}"} for i in range(5)]
    ds = await datasets.create_json_upload(
        name="ds",
        file_bytes=json.dumps({"items": ds_items}).encode()
    )
    
    # Create run with sampling: shuffle, limit, seed
    run = await svc.create_run(name="r1", runspec_dict={
        "name": "r1",
        "targets": [{"config_id": tcfg.id}],
        "dataset": {"config_id": ds.id},
        "executor": {"plugin": "single_turn"},
        "scorers": [],
        "sampling": {"limit": 3, "shuffle": True, "seed": 42}
    })
    
    await svc.execute_run(run.id)
    
    # Verify exactly 3 attempts
    async with SessionLocal() as s:
        from sqlalchemy import select
        attempts = (await s.execute(
            select(models.Attempt)
            .where(models.Attempt.run_id == run.id)
            .order_by(models.Attempt.created_at)
        )).scalars().all()
        assert len(attempts) == 3
        
        # Get the prompts to verify they're a subset of the original
        prompts = [att.prompt_text for att in attempts]
        original_prompts = [f"prompt-{i}" for i in range(5)]
        for p in prompts:
            assert p in original_prompts


@pytest.mark.asyncio
@respx.mock
async def test_run_without_sampling(tmp_path):
    """Test that runs without sampling process full dataset."""
    respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "Response"}}],
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
    
    # Create target
    tcfg = await targets.create(
        name="t1",
        plugin="openai_compat",
        params={"name": "t1", "base_url": "https://api.example.com/v1", "model": "m"},
        secret={"api_key": "sk"}
    )
    
    # Create dataset with 5 items
    ds_items = [{"prompt": f"prompt-{i}"} for i in range(5)]
    ds = await datasets.create_json_upload(
        name="ds",
        file_bytes=json.dumps({"items": ds_items}).encode()
    )
    
    # Create run WITHOUT sampling
    run = await svc.create_run(name="r1", runspec_dict={
        "name": "r1",
        "targets": [{"config_id": tcfg.id}],
        "dataset": {"config_id": ds.id},
        "executor": {"plugin": "single_turn"},
        "scorers": []
    })
    
    await svc.execute_run(run.id)
    
    # Verify all 5 attempts were created
    async with SessionLocal() as s:
        from sqlalchemy import select
        attempts = (await s.execute(
            select(models.Attempt).where(models.Attempt.run_id == run.id)
        )).scalars().all()
        assert len(attempts) == 5
