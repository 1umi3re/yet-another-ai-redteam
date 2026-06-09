import asyncio
import json

import httpx
import pytest
import respx
from cryptography.fernet import Fernet
from sqlalchemy import select

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
async def test_run_service_runs_executor_methods_and_filters_by_item_language(tmp_path):
    calls: list[str] = []

    class EchoTarget:
        def __init__(self, *, name: str) -> None:
            self.name = name

        async def generate(self, prompt):
            calls.append(prompt.text)
            return Response(text=f"ok:{prompt.text}", raw={}, latency_ms=1)

        async def aclose(self):
            pass

    default_registry().register("targets", "executor_method_echo_target", EchoTarget)

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

    tcfg = await targets.create(name="t1", plugin="executor_method_echo_target", params={"name": "t1"})
    ds = await datasets.create_json_upload(
        name="mixed",
        file_bytes=json.dumps({"items": [{"id": "en", "prompt": "hello"}, {"id": "zh", "prompt": "你好"}]}).encode(),
    )
    run = await svc.create_run(
        name="r1",
        runspec_dict={
            "version": 2,
            "name": "r1",
            "targets": [{"config_id": tcfg.id}],
            "dataset": {"config_id": ds.id},
            "executors": [
                {"kind": "executor", "plugin": "single_turn"},
                {"kind": "converter_method", "plugin": "base64", "params": {"wrap": False}},
            ],
        },
    )

    await svc.execute_run(run.id)

    async with SessionLocal() as s:
        attempts = (
            (
                await s.execute(
                    select(models.Attempt).where(models.Attempt.run_id == run.id).order_by(models.Attempt.created_at)
                )
            )
            .scalars()
            .all()
        )
        run_row = await s.get(models.Run, run.id)

    assert run_row.status == "completed"
    assert run_row.progress_done == 3
    assert run_row.progress_total == 3
    assert [(a.executor_name, a.dataset_item_id, a.dataset_item_language) for a in attempts] == [
        ("single_turn", "en", "en"),
        ("base64", "en", "en"),
        ("single_turn", "zh", "zh"),
    ]
    assert [a.prompt_text for a in attempts] == ["hello", "aGVsbG8=", "你好"]
    assert calls == ["hello", "aGVsbG8=", "你好"]

    content = await datasets.content(ds.id)
    assert [item["language"] for item in content["items"]] == ["en", "zh"]


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
async def test_run_service_pauses_at_attempt_boundary_and_resumes(tmp_path):
    started = asyncio.Event()
    release = asyncio.Event()
    calls: list[str] = []

    class BlockingTarget:
        def __init__(self, *, name: str) -> None:
            self.name = name

        async def generate(self, prompt):
            calls.append(prompt.text)
            if len(calls) == 1:
                started.set()
                await release.wait()
            return Response(text=f"ok:{prompt.text}", raw={}, latency_ms=1)

        async def aclose(self):
            pass

    default_registry().register("targets", "blocking_pause_target", BlockingTarget)

    engine_db = make_engine(f"sqlite+aiosqlite:///{tmp_path}/x.db")
    SessionLocal = make_sessionmaker(engine_db)
    async with engine_db.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    blob = LocalBlobStore(tmp_path / "blobs")
    box = SecretBox(Fernet.generate_key().decode())
    targets = TargetConfigService(SessionLocal, box)
    datasets = DatasetService(SessionLocal, blob)
    bus = ProgressBus()
    svc = RunService(SessionLocal, blob, box, targets, datasets, bus, max_concurrency=1)

    tcfg = await targets.create(name="t1", plugin="blocking_pause_target", params={"name": "t1"})
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
            "concurrency": 1,
        },
    )

    await svc.start_run(run.id)
    await asyncio.wait_for(started.wait(), timeout=1)
    await svc.pause_run(run.id)

    async with SessionLocal() as s:
        assert (await s.get(models.Run, run.id)).status == "pausing"

    release.set()
    for _ in range(50):
        async with SessionLocal() as s:
            run_row = await s.get(models.Run, run.id)
            attempts = (await s.execute(select(models.Attempt).where(models.Attempt.run_id == run.id))).scalars().all()
        if run_row.status == "paused":
            break
        await asyncio.sleep(0.02)

    assert run_row.status == "paused"
    assert run_row.progress_done == 1
    assert run_row.progress_total == 3
    assert [a.prompt_text for a in attempts] == ["a"]
    assert len({a.work_key for a in attempts}) == 1

    await svc.resume_run(run.id)
    for _ in range(50):
        async with SessionLocal() as s:
            run_row = await s.get(models.Run, run.id)
            attempts = (
                (
                    await s.execute(
                        select(models.Attempt)
                        .where(models.Attempt.run_id == run.id)
                        .order_by(models.Attempt.created_at)
                    )
                )
                .scalars()
                .all()
            )
        if run_row.status in {"completed", "failed"}:
            break
        await asyncio.sleep(0.02)

    assert run_row.status == "completed"
    assert run_row.progress_done == 3
    assert [a.prompt_text for a in attempts] == ["a", "b", "c"]
    assert calls == ["a", "b", "c"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("retry_failed", "expected_statuses", "expected_calls"),
    [
        (False, ["completed", "failed", "completed"], ["a", "b", "c"]),
        (True, ["completed", "completed", "completed"], ["a", "b", "b", "c"]),
    ],
)
async def test_run_service_resume_failed_work_retry_option(
    tmp_path, retry_failed, expected_statuses, expected_calls
):
    second_started = asyncio.Event()
    release_second = asyncio.Event()
    calls: list[str] = []
    failed_once = False

    class RetryTarget:
        def __init__(self, *, name: str) -> None:
            self.name = name

        async def generate(self, prompt):
            nonlocal failed_once
            calls.append(prompt.text)
            if prompt.text == "b" and not failed_once:
                second_started.set()
                await release_second.wait()
                failed_once = True
                raise RuntimeError("temporary target failure")
            return Response(text=f"ok:{prompt.text}", raw={}, latency_ms=1)

        async def aclose(self):
            pass

    default_registry().register("targets", "retry_pause_target", RetryTarget)

    engine_db = make_engine(f"sqlite+aiosqlite:///{tmp_path}/x.db")
    SessionLocal = make_sessionmaker(engine_db)
    async with engine_db.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    blob = LocalBlobStore(tmp_path / "blobs")
    box = SecretBox(Fernet.generate_key().decode())
    targets = TargetConfigService(SessionLocal, box)
    datasets = DatasetService(SessionLocal, blob)
    bus = ProgressBus()
    svc = RunService(SessionLocal, blob, box, targets, datasets, bus, max_concurrency=1)

    tcfg = await targets.create(name="t1", plugin="retry_pause_target", params={"name": "t1"})
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
            "concurrency": 1,
        },
    )

    await svc.start_run(run.id)
    await asyncio.wait_for(second_started.wait(), timeout=1)
    await svc.pause_run(run.id)
    release_second.set()

    for _ in range(50):
        async with SessionLocal() as s:
            run_row = await s.get(models.Run, run.id)
        if run_row.status == "paused":
            break
        await asyncio.sleep(0.02)

    assert run_row.status == "paused"

    await svc.resume_run(run.id, retry_failed=retry_failed)
    for _ in range(50):
        async with SessionLocal() as s:
            run_row = await s.get(models.Run, run.id)
            attempts = (
                (
                    await s.execute(
                        select(models.Attempt)
                        .where(models.Attempt.run_id == run.id)
                        .order_by(models.Attempt.prompt_text)
                    )
                )
                .scalars()
                .all()
            )
        if run_row.status in {"completed", "failed"}:
            break
        await asyncio.sleep(0.02)

    assert run_row.status == "completed"
    assert run_row.progress_done == 3
    assert [a.prompt_text for a in attempts] == ["a", "b", "c"]
    assert [a.status for a in attempts] == expected_statuses
    assert calls == expected_calls


@pytest.mark.asyncio
async def test_run_service_resumes_remaining_work_after_failed_run(tmp_path):
    calls: list[str] = []

    class TimeoutOnceTarget:
        def __init__(self, *, name: str) -> None:
            self.name = name

        async def generate(self, prompt):
            calls.append(prompt.text)
            if prompt.text == "b" and calls.count("b") == 1:
                await asyncio.sleep(0.2)
            return Response(text=f"ok:{prompt.text}", raw={}, latency_ms=1)

        async def aclose(self):
            pass

    default_registry().register("targets", "resume_failed_timeout_target", TimeoutOnceTarget)

    engine_db = make_engine(f"sqlite+aiosqlite:///{tmp_path}/x.db")
    SessionLocal = make_sessionmaker(engine_db)
    async with engine_db.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    blob = LocalBlobStore(tmp_path / "blobs")
    box = SecretBox(Fernet.generate_key().decode())
    targets = TargetConfigService(SessionLocal, box)
    datasets = DatasetService(SessionLocal, blob)
    bus = ProgressBus()
    svc = RunService(SessionLocal, blob, box, targets, datasets, bus, max_concurrency=1)

    tcfg = await targets.create(name="t1", plugin="resume_failed_timeout_target", params={"name": "t1"})
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
            "concurrency": 1,
            "timeout_seconds": 0.05,
        },
    )

    with pytest.raises(TimeoutError):
        await svc.execute_run(run.id)

    async with SessionLocal() as s:
        run_row = await s.get(models.Run, run.id)
        attempts = (
            (
                await s.execute(
                    select(models.Attempt).where(models.Attempt.run_id == run.id).order_by(models.Attempt.prompt_text)
                )
            )
            .scalars()
            .all()
        )
    assert run_row.status == "failed"
    assert [a.prompt_text for a in attempts] == ["a"]

    await svc.resume_run(run.id, retry_failed=False)
    for _ in range(50):
        async with SessionLocal() as s:
            run_row = await s.get(models.Run, run.id)
            attempts = (
                (
                    await s.execute(
                        select(models.Attempt)
                        .where(models.Attempt.run_id == run.id)
                        .order_by(models.Attempt.prompt_text)
                    )
                )
                .scalars()
                .all()
            )
        if run_row.status in {"completed", "failed"} and len(attempts) == 3:
            break
        await asyncio.sleep(0.02)

    assert run_row.status == "completed"
    assert run_row.error is None
    assert run_row.progress_done == 3
    assert [a.prompt_text for a in attempts] == ["a", "b", "c"]
    assert calls == ["a", "b", "b", "c"]


@pytest.mark.asyncio
async def test_run_timeout_cancels_in_flight_attempt_writes(tmp_path):
    calls: list[str] = []

    class SlowTarget:
        def __init__(self, *, name: str) -> None:
            self.name = name

        async def generate(self, prompt):
            calls.append(prompt.text)
            await asyncio.sleep(0.2)
            return Response(text=f"late:{prompt.text}", raw={}, latency_ms=1)

        async def aclose(self):
            pass

    default_registry().register("targets", "timeout_cancel_target", SlowTarget)

    engine_db = make_engine(f"sqlite+aiosqlite:///{tmp_path}/x.db")
    SessionLocal = make_sessionmaker(engine_db)
    async with engine_db.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    blob = LocalBlobStore(tmp_path / "blobs")
    box = SecretBox(Fernet.generate_key().decode())
    targets = TargetConfigService(SessionLocal, box)
    datasets = DatasetService(SessionLocal, blob)
    bus = ProgressBus()
    svc = RunService(SessionLocal, blob, box, targets, datasets, bus, max_concurrency=2)

    tcfg = await targets.create(name="t1", plugin="timeout_cancel_target", params={"name": "t1"})
    ds = await datasets.create_json_upload(
        name="ds",
        file_bytes=json.dumps({"items": [{"prompt": "a"}, {"prompt": "b"}]}).encode(),
    )
    run = await svc.create_run(
        name="r1",
        runspec_dict={
            "name": "r1",
            "targets": [{"config_id": tcfg.id}],
            "dataset": {"config_id": ds.id},
            "executor": {"plugin": "single_turn"},
            "concurrency": 2,
            "timeout_seconds": 0.05,
        },
    )

    with pytest.raises(TimeoutError):
        await svc.execute_run(run.id)
    await asyncio.sleep(0.25)

    async with SessionLocal() as s:
        run_row = await s.get(models.Run, run.id)
        attempts = (await s.execute(select(models.Attempt).where(models.Attempt.run_id == run.id))).scalars().all()

    assert run_row.status == "failed"
    assert run_row.progress_done == 0
    assert attempts == []
    assert sorted(calls) == ["a", "b"]


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
