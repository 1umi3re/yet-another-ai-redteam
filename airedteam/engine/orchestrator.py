from __future__ import annotations

from collections.abc import AsyncIterator

from airedteam.core.types import Prompt


class DefaultOrchestrator:
    name = "default"

    async def attempts(self, dataset, converters) -> AsyncIterator[Prompt]:
        async for p in dataset:
            yield p
