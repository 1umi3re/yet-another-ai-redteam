from __future__ import annotations
import asyncio
from typing import Any, Awaitable, Callable
from airedteam.core.types import AttemptResult, ScoreResult


class RunEngine:
    """Fan-out sample × target, execute, score, invoke callbacks, publish events."""

    def __init__(
        self,
        *,
        progress_bus,
        on_attempt: Callable[[AttemptResult, str, str | None], Awaitable[None]],
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
        converters: list,
        executor,
        scorers: list,
        concurrency: int,
        orchestrator,
    ) -> None:
        sem = asyncio.Semaphore(max(1, concurrency))
        converter_variants = [[c] for c in converters] if converters else [[]]
        target_sems: dict[int, asyncio.Semaphore] = {}
        for target in targets:
            limit = getattr(target, "_airedteam_max_concurrency", None)
            if limit is not None:
                target_sems[id(target)] = asyncio.Semaphore(max(1, int(limit)))

        async def process(prompt, target, converter_variant):
            target_name = getattr(target, "name", "?")
            dataset_item_id = None
            try:
                dataset_item_id = prompt.metadata.get("id")
            except Exception:
                pass
            target_sem = target_sems.get(id(target))
            if target_sem is not None:
                async with target_sem:
                    async with sem:
                        await run_attempt(prompt, target, converter_variant, target_name, dataset_item_id)
            else:
                async with sem:
                    await run_attempt(prompt, target, converter_variant, target_name, dataset_item_id)

        async def run_attempt(prompt, target, converter_variant, target_name, dataset_item_id):
            ar = await executor.run(prompt, target, converter_variant)
            async with self._lock:
                await self._on_attempt(ar, target_name, dataset_item_id)
                idx = self._counter
                self._counter += 1
            await self._bus.publish(run_id, {"type": "attempt.completed", "status": ar.status})
            for sc in scorers:
                try:
                    sr = await sc.score(ar)
                except Exception as e:
                    sr = ScoreResult(scorer=getattr(sc, "name", "?"), value={"error": str(e)}, rationale=None)
                await self._on_score(idx, sr)

        tasks: list[asyncio.Task] = []
        async for prompt in orchestrator.attempts(dataset, converters):
            for t in targets:
                for converter_variant in converter_variants:
                    tasks.append(asyncio.create_task(process(prompt, t, converter_variant)))
        if tasks:
            await asyncio.gather(*tasks)
