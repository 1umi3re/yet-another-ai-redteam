from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any


class ProgressBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, run_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subs[run_id].append(q)
        return q

    def unsubscribe(self, run_id: str, q: asyncio.Queue) -> None:
        lst = self._subs.get(run_id)
        if lst and q in lst:
            lst.remove(q)

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        for q in list(self._subs.get(run_id, [])):
            await q.put(event)
