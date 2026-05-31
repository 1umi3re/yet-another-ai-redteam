from __future__ import annotations

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
async def test_pair_end_to_end(tmp_path):
    target_replies = iter(
        [
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "refused"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "sure here"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
        ]
    )
    respx.post("https://target.example.com/v1/chat/completions").mock(side_effect=lambda req: next(target_replies))
    respx.post("https://attacker.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"prompt": "refined", "improvement": "x"}'}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
    )
    judge_replies = iter(
        [
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": '{"score": 3, "rationale": "refused"}'}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": '{"score": 10, "rationale": "complied"}'}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
        ]
    )
    respx.post("https://judge.example.com/v1/chat/completions").mock(side_effect=lambda req: next(judge_replies))

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

    tgt_cfg = await targets.create(
        name="t",
        plugin="openai_compat",
        params={"name": "t", "base_url": "https://target.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    atk_cfg = await targets.create(
        name="a",
        plugin="openai_compat",
        params={"name": "a", "base_url": "https://attacker.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    jdg_cfg = await targets.create(
        name="j",
        plugin="openai_compat",
        params={"name": "j", "base_url": "https://judge.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    ds = await datasets.create_json_upload(name="ds", file_bytes=json.dumps({"items": [{"prompt": "seed"}]}).encode())

    run = await svc.create_run(
        name="r",
        runspec_dict={
            "name": "r",
            "targets": [{"config_id": tgt_cfg.id}],
            "dataset": {"config_id": ds.id},
            "executor": {
                "plugin": "pair",
                "params": {
                    "attacker_config_id": atk_cfg.id,
                    "judge_config_id": jdg_cfg.id,
                    "goal": "get X",
                    "max_turns": "5",
                    "success_threshold": "8",
                },
            },
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
        assert a.response_text == "sure here"

    payload = json.loads((await blob.get(a.conversation_blob_path)).decode("utf-8"))
    roles = [m["role"] for m in payload["messages"]]
    assert roles == ["user", "assistant", "user", "assistant"]


@pytest.mark.asyncio
@respx.mock
async def test_jailbreak_iterative_end_to_end(tmp_path):
    target_replies = iter(
        [
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "refused"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "sure here"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
        ]
    )
    respx.post("https://target.example.com/v1/chat/completions").mock(side_effect=lambda req: next(target_replies))
    respx.post("https://attacker.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"prompt": "refined", "improvement": "x"}'}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
    )
    judge_replies = iter(
        [
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": '{"score": 3, "rationale": "refused"}'}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": '{"score": 10, "rationale": "complied"}'}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
        ]
    )
    respx.post("https://judge.example.com/v1/chat/completions").mock(side_effect=lambda req: next(judge_replies))

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

    tgt_cfg = await targets.create(
        name="t",
        plugin="openai_compat",
        params={"name": "t", "base_url": "https://target.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    atk_cfg = await targets.create(
        name="a",
        plugin="openai_compat",
        params={"name": "a", "base_url": "https://attacker.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    jdg_cfg = await targets.create(
        name="j",
        plugin="openai_compat",
        params={"name": "j", "base_url": "https://judge.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    ds = await datasets.create_json_upload(name="ds", file_bytes=json.dumps({"items": [{"prompt": "seed"}]}).encode())

    run = await svc.create_run(
        name="r",
        runspec_dict={
            "name": "r",
            "targets": [{"config_id": tgt_cfg.id}],
            "dataset": {"config_id": ds.id},
            "executor": {
                "plugin": "jailbreak_iterative",
                "params": {
                    "attacker_config_id": atk_cfg.id,
                    "judge_config_id": jdg_cfg.id,
                    "goal": "get X",
                    "max_turns": "5",
                    "success_threshold": "8",
                },
            },
        },
    )
    await svc.execute_run(run.id)

    from sqlalchemy import select

    async with SessionLocal() as s:
        attempt = (await s.execute(select(models.Attempt).where(models.Attempt.run_id == run.id))).scalar_one()
        assert attempt.conversation_blob_path is not None
        assert attempt.response_text == "sure here"

    payload = json.loads((await blob.get(attempt.conversation_blob_path)).decode("utf-8"))
    assert [m["role"] for m in payload["messages"]] == ["user", "assistant", "user", "assistant"]
