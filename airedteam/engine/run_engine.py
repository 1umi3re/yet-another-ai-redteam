from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from airedteam.core.score_status import exception_detail, failed_score_value
from airedteam.core.types import AttemptResult, Prompt, ScoreResult


@dataclass(frozen=True)
class WorkItem:
    prompt: Prompt
    prompt_index: int
    target: Any
    target_index: int
    target_name: str
    converter_variant: list
    converter_index: int
    executor_variant: ExecutorVariant | None
    executor_index: int
    dataset_item_id: str | None
    dataset_item_language: str | None
    work_key: str


@dataclass(frozen=True)
class ExecutorVariant:
    kind: str
    plugin: str
    executor: Any
    language_support: set[str] | frozenset[str]


@dataclass(frozen=True)
class RunEngineResult:
    stopped: bool = False


def work_key_for(
    *,
    prompt: Prompt,
    prompt_index: int,
    target_index: int,
    target_name: str,
    converter_variant: list,
    converter_index: int,
) -> str:
    prompt_id = None
    try:
        prompt_id = prompt.metadata.get("id")
    except Exception:
        pass
    payload = {
        "version": 1,
        "prompt_index": prompt_index,
        "prompt_id": prompt_id,
        "prompt_sha256": hashlib.sha256(prompt.text.encode("utf-8", errors="ignore")).hexdigest(),
        "target_index": target_index,
        "target_name": target_name,
        "converter_index": converter_index,
        "converter_names": [getattr(c, "name", type(c).__name__) for c in converter_variant],
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=repr)
    return "v1:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def work_key_for_executor(
    *,
    prompt: Prompt,
    prompt_index: int,
    target_index: int,
    target_name: str,
    executor_variant: ExecutorVariant,
    executor_index: int,
) -> str:
    prompt_id = None
    try:
        prompt_id = prompt.metadata.get("id")
    except Exception:
        pass
    payload = {
        "version": 2,
        "prompt_index": prompt_index,
        "prompt_id": prompt_id,
        "prompt_sha256": hashlib.sha256(prompt.text.encode("utf-8", errors="ignore")).hexdigest(),
        "target_index": target_index,
        "target_name": target_name,
        "executor_index": executor_index,
        "executor_kind": executor_variant.kind,
        "executor_plugin": executor_variant.plugin,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=repr)
    return "v2:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


class RunEngine:
    """Fan-out sample × target, execute, score, invoke callbacks, publish events."""

    def __init__(
        self,
        *,
        progress_bus,
        on_attempt: Callable[[AttemptResult, str, str | None, str, Prompt], Awaitable[None]],
        on_score: Callable[[int, ScoreResult], Awaitable[None]],
    ) -> None:
        self._bus = progress_bus
        self._on_attempt = on_attempt
        self._on_score = on_score
        self._counter = 0
        self._lock = asyncio.Lock()

    async def run(
        self,
        *,
        run_id: str,
        dataset,
        targets: list,
        scorers: list,
        concurrency: int,
        orchestrator,
        converters: list | None = None,
        executor=None,
        executor_variants: list[ExecutorVariant] | None = None,
        should_stop: Callable[[], Awaitable[bool]] | None = None,
        should_skip_work: Callable[[str], Awaitable[bool]] | None = None,
        on_language_filtered: Callable[[dict], Any] | None = None,
    ) -> RunEngineResult:
        max_active = max(1, concurrency)
        converters = converters or []
        legacy_mode = executor_variants is None
        converter_variants = [[c] for c in converters] if converters else [[]]
        active_executor_variants = executor_variants or []
        target_sems: dict[int, asyncio.Semaphore] = {}
        for target in targets:
            limit = getattr(target, "_airedteam_max_concurrency", None)
            if limit is not None:
                target_sems[id(target)] = asyncio.Semaphore(max(1, int(limit)))

        async def stop_requested() -> bool:
            return bool(should_stop is not None and await should_stop())

        async def process(item: WorkItem):
            target_sem = target_sems.get(id(item.target))
            if target_sem is not None:
                async with target_sem:
                    if not await stop_requested():
                        await run_attempt(item)
            elif not await stop_requested():
                await run_attempt(item)

        async def run_attempt(item: WorkItem):
            active_executor = item.executor_variant.executor if item.executor_variant is not None else executor
            executor_name = item.executor_variant.plugin if item.executor_variant is not None else None
            executor_kind = item.executor_variant.kind if item.executor_variant is not None else "executor"
            try:
                ar = await active_executor.run(item.prompt, item.target, item.converter_variant)
            except Exception as e:
                ar = AttemptResult(
                    prompt=item.prompt,
                    response=None,
                    status="failed",
                    error=exception_detail(e),
                    converter_chain=[getattr(c, "name", type(c).__name__) for c in item.converter_variant],
                )
            ar.executor_name = ar.executor_name or executor_name or (
                (ar.converter_chain or [None])[0] or getattr(active_executor, "name", type(active_executor).__name__)
            )
            ar.executor_kind = ar.executor_kind or executor_kind
            ar.dataset_item_language = ar.dataset_item_language or item.dataset_item_language
            async with self._lock:
                await self._on_attempt(ar, item.target_name, item.dataset_item_id, item.work_key, item.prompt)
                idx = self._counter
                self._counter += 1
            await self._bus.publish(
                run_id,
                {"type": "attempt.completed", "status": ar.status, "work_key": item.work_key},
            )
            for sc in scorers:
                try:
                    sr = await sc.score(ar)
                except Exception as e:
                    sr = ScoreResult(scorer=getattr(sc, "name", "?"), value=failed_score_value(e), rationale=None)
                await self._on_score(idx, sr)

        async def wait_for_slot(active: set[asyncio.Task]) -> set[asyncio.Task]:
            if len(active) < max_active:
                return active
            done, pending = await asyncio.wait(active, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                await task
            return set(pending)

        async def drain(active: set[asyncio.Task]) -> None:
            while active:
                done, pending = await asyncio.wait(active, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    await task
                active = set(pending)

        active: set[asyncio.Task] = set()
        stopped = False
        try:
            prompt_index = -1
            async for prompt in orchestrator.attempts(dataset, converters):
                prompt_index += 1
                for target_index, target in enumerate(targets):
                    target_name = getattr(target, "name", "?")
                    dataset_item_id = None
                    try:
                        dataset_item_id = prompt.metadata.get("id")
                    except Exception:
                        pass
                    try:
                        dataset_item_language = prompt.metadata.get("language")
                    except Exception:
                        dataset_item_language = None
                    if legacy_mode:
                        variants = [
                            (None, idx, converter_variant)
                            for idx, converter_variant in enumerate(converter_variants)
                        ]
                    else:
                        variants = [
                            (executor_variant, idx, [])
                            for idx, executor_variant in enumerate(active_executor_variants)
                        ]
                    for executor_variant, variant_index, converter_variant in variants:
                        if executor_variant is not None:
                            language_support = set(executor_variant.language_support or [])
                            if dataset_item_language not in language_support:
                                if on_language_filtered is not None:
                                    payload = {
                                        "executor_name": executor_variant.plugin,
                                        "executor_kind": executor_variant.kind,
                                        "language": dataset_item_language,
                                        "target_name": target_name,
                                        "dataset_item_id": dataset_item_id,
                                    }
                                    maybe_awaitable = on_language_filtered(payload)
                                    if inspect.isawaitable(maybe_awaitable):
                                        await maybe_awaitable
                                continue
                        active = await wait_for_slot(active)
                        if await stop_requested():
                            stopped = True
                            break
                        if executor_variant is None:
                            work_key = work_key_for(
                                prompt=prompt,
                                prompt_index=prompt_index,
                                target_index=target_index,
                                target_name=target_name,
                                converter_variant=converter_variant,
                                converter_index=variant_index,
                            )
                        else:
                            work_key = work_key_for_executor(
                                prompt=prompt,
                                prompt_index=prompt_index,
                                target_index=target_index,
                                target_name=target_name,
                                executor_variant=executor_variant,
                                executor_index=variant_index,
                            )
                        if should_skip_work is not None and await should_skip_work(work_key):
                            continue
                        item = WorkItem(
                            prompt=prompt,
                            prompt_index=prompt_index,
                            target=target,
                            target_index=target_index,
                            target_name=target_name,
                            converter_variant=converter_variant,
                            converter_index=variant_index,
                            executor_variant=executor_variant,
                            executor_index=variant_index,
                            dataset_item_id=dataset_item_id,
                            dataset_item_language=dataset_item_language,
                            work_key=work_key,
                        )
                        active.add(asyncio.create_task(process(item)))
                    if stopped:
                        break
                if stopped:
                    break

            await drain(active)
        except BaseException:
            for task in active:
                task.cancel()
            await asyncio.gather(*active, return_exceptions=True)
            raise
        if not stopped and await stop_requested():
            stopped = True
        return RunEngineResult(stopped=stopped)
