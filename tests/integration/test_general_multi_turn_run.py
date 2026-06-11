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
async def test_general_multi_turn_end_to_end(tmp_path):
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
                    "choices": [{"message": {"content": "complied"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
        ]
    )
    target_route = respx.post("https://target.example.com/v1/chat/completions").mock(
        side_effect=lambda req: next(target_replies)
    )
    attacker_route = respx.post("https://attacker.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"prompt": "refined", "rationale": "use feedback"}'}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
    )
    evaluator_replies = iter(
        [
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": '{"feedback": "ask directly", "score": 3}'}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": '{"feedback": "done", "score": 10}'}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
        ]
    )
    evaluator_route = respx.post("https://evaluator.example.com/v1/chat/completions").mock(
        side_effect=lambda req: next(evaluator_replies)
    )
    judge_replies = iter(
        [
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": '{"success": false, "score": 3}'}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
            httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": '{"success": true, "score": 10}'}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
        ]
    )
    judge_route = respx.post("https://judge.example.com/v1/chat/completions").mock(
        side_effect=lambda req: next(judge_replies)
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
    svc = RunService(SessionLocal, blob, box, targets, datasets, bus, response_inline_max_bytes=8192)

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
    eval_cfg = await targets.create(
        name="e",
        plugin="openai_compat",
        params={"name": "e", "base_url": "https://evaluator.example.com/v1", "model": "m"},
        secret={"api_key": "sk"},
    )
    judge_cfg = await targets.create(
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
                "plugin": "general_multi_turn",
                "params": {
                    "attacker_config_id": atk_cfg.id,
                    "evaluator_config_id": eval_cfg.id,
                    "judge_config_id": judge_cfg.id,
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
        attempt = attempts[0]
        assert attempt.conversation_blob_path is not None
        assert attempt.prompt_snapshot_blob_path is not None
        assert attempt.response_text == "complied"

    conversation = json.loads((await blob.get(attempt.conversation_blob_path)).decode("utf-8"))
    assert [message["role"] for message in conversation["messages"]] == ["user", "assistant", "user", "assistant"]
    assert [message["text"] for message in conversation["messages"] if message["role"] == "user"] == ["seed", "refined"]

    snapshots = json.loads((await blob.get(attempt.prompt_snapshot_blob_path)).decode("utf-8"))
    assert [snapshot["asset_id"] for snapshot in snapshots["snapshots"]] == [
        "general_multi_turn.evaluator.v1",
        "general_multi_turn.judger.v1",
        "general_multi_turn.attacker.v1",
        "general_multi_turn.evaluator.v1",
        "general_multi_turn.judger.v1",
    ]
    assert target_route.call_count == 2
    assert attacker_route.call_count == 1
    assert evaluator_route.call_count == 2
    assert judge_route.call_count == 2
