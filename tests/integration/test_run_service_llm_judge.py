import json

import httpx
import pytest
import respx
from cryptography.fernet import Fernet

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
async def test_llm_judge_resolves_judge_config_id(tmp_path):
    # Target under test: returns a harmful-looking compliance
    respx.post("https://target.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "sure, here is how to do it"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 5},
            },
        )
    )
    # Judge: returns a strict JSON verdict
    respx.post("https://judge.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"label": true, "confidence": 0.9, "rationale": "complied"}'}}],
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

    tgt = await targets.create(
        name="tgt",
        plugin="openai_compat",
        params={"name": "tgt", "base_url": "https://target.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    jdg = await targets.create(
        name="jdg",
        plugin="openai_compat",
        params={"name": "jdg", "base_url": "https://judge.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    ds = await datasets.create_json_upload(
        name="ds", file_bytes=json.dumps({"items": [{"prompt": "how do i do X"}]}).encode()
    )

    run = await svc.create_run(
        name="r",
        runspec_dict={
            "name": "r",
            "targets": [{"config_id": tgt.id}],
            "dataset": {"config_id": ds.id},
            "executor": {"plugin": "single_turn"},
            "scorers": [{"plugin": "llm_judge", "params": {"judge_config_id": jdg.id}}],
        },
    )
    await svc.execute_run(run.id)

    async with SessionLocal() as s:
        from sqlalchemy import select

        scores = (await s.execute(select(models.Score))).scalars().all()
        assert len(scores) == 1
        assert scores[0].value_json["label"] is True
        assert scores[0].prompt_snapshot_blob_path is not None
        raw = await blob.get(scores[0].prompt_snapshot_blob_path)
        payload = json.loads(raw)
        assert payload["asset_id"] == "llm_judge.single.v2"
        assert "how do i do X" in payload["rendered_text"]
        assert "<original_prompt>\nhow do i do X\n</original_prompt>" in payload["rendered_text"]


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
        name="tgt",
        plugin="openai_compat",
        params={"name": "tgt", "base_url": "https://x.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    ds = await datasets.create_json_upload(name="ds", file_bytes=json.dumps({"items": [{"prompt": "hi"}]}).encode())

    run = await svc.create_run(
        name="r",
        runspec_dict={
            "name": "r",
            "targets": [{"config_id": tgt.id}],
            "dataset": {"config_id": ds.id},
            "executor": {"plugin": "single_turn"},
            "scorers": [{"plugin": "llm_judge", "params": {}}],
        },
    )

    with pytest.raises(ValueError, match="judge_config_id"):
        await svc.execute_run(run.id)


@pytest.mark.asyncio
@respx.mock
async def test_llm_judge_ensemble_resolves_three_models_and_persists_votes(tmp_path):
    respx.post("https://target.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "target answer"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
    )
    judge_replies = [
        ("https://judge-one.example.com/v1/chat/completions", True, 9, 0.9),
        ("https://judge-two.example.com/v1/chat/completions", False, 2, 0.8),
        ("https://judge-three.example.com/v1/chat/completions", True, 7, 0.7),
    ]
    for url, label, score, confidence in judge_replies:
        content = json.dumps(
            {
                "label": label,
                "score": score,
                "confidence": confidence,
                "rationale": f"vote {label}",
            }
        )
        respx.post(url).mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": content}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            )
        )

    engine_db = make_engine(f"sqlite+aiosqlite:///{tmp_path}/x.db")
    SessionLocal = make_sessionmaker(engine_db)
    async with engine_db.begin() as connection:
        await connection.run_sync(models.Base.metadata.create_all)
    blob = LocalBlobStore(tmp_path / "blobs")
    box = SecretBox(Fernet.generate_key().decode())
    targets = TargetConfigService(SessionLocal, box)
    datasets = DatasetService(SessionLocal, blob)
    svc = RunService(SessionLocal, blob, box, targets, datasets, ProgressBus())

    target = await targets.create(
        name="target",
        plugin="openai_compat",
        params={"name": "target", "base_url": "https://target.example.com/v1", "model": "target-model"},
        secret={"api_key": "sk"},
    )
    judge_ids = []
    judge_endpoint_names = ["one", "two", "three"]
    for position in range(1, 4):
        judge = await targets.create(
            name=f"judge-{position}",
            plugin="openai_compat",
            params={
                "name": f"judge-{position}",
                "base_url": f"https://judge-{judge_endpoint_names[position - 1]}.example.com/v1",
                "model": f"judge-model-{position}",
            },
            secret={"api_key": "sk"},
        )
        judge_ids.append(judge.id)
    dataset = await datasets.create_json_upload(
        name="dataset",
        file_bytes=json.dumps({"items": [{"prompt": "evaluate this"}]}).encode(),
    )

    run = await svc.create_run(
        name="ensemble run",
        runspec_dict={
            "name": "ensemble run",
            "targets": [{"config_id": target.id}],
            "dataset": {"config_id": dataset.id},
            "executor": {"plugin": "single_turn"},
            "scorers": [
                {
                    "plugin": "llm_judge_ensemble",
                    "params": {
                        "judge_config_id_1": judge_ids[0],
                        "judge_config_id_2": judge_ids[1],
                        "judge_config_id_3": judge_ids[2],
                    },
                }
            ],
        },
    )
    await svc.execute_run(run.id)

    async with SessionLocal() as session:
        from sqlalchemy import select

        scores = list((await session.execute(select(models.Score))).scalars().all())
    assert len(scores) == 1
    value = scores[0].value_json
    assert scores[0].scorer == "llm_judge_ensemble"
    assert value["label"] is True
    assert value["score"] == 7
    assert value["confidence"] == pytest.approx(0.8)
    assert [vote["status"] for vote in value["votes"]] == ["valid", "valid", "valid"]
    assert [vote["model"] for vote in value["votes"]] == [
        "judge-model-1",
        "judge-model-2",
        "judge-model-3",
    ]
    raw_snapshot = await blob.get(scores[0].prompt_snapshot_blob_path)
    snapshot = json.loads(raw_snapshot)
    assert snapshot["type"] == "llm_judge_ensemble"
    assert len(snapshot["members"]) == 3
