from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from airedteam.core.types import Prompt


class HuggingFaceDataset:
    name = "hf"

    def __init__(
        self,
        *,
        repo: str,
        split: str = "train",
        prompt_field: str = "prompt",
        id_field: str | None = None,
        limit: int | None = None,
        hf_token: str | None = None,
    ) -> None:
        self.repo = repo
        self.split = split
        self.prompt_field = prompt_field
        self.id_field = id_field
        self.limit = limit
        self.hf_token = hf_token

    async def _iter_rows(self):
        from datasets import load_dataset

        ds = await asyncio.to_thread(load_dataset, self.repo, split=self.split, streaming=True, token=self.hf_token)
        for i, row in enumerate(ds):
            yield i, row

    async def __aiter__(self) -> AsyncIterator[Prompt]:
        n = 0
        async for i, row in self._iter_rows():
            if self.limit is not None and n >= self.limit:
                return
            text = row[self.prompt_field]
            meta = {"id": str(row[self.id_field]) if self.id_field else str(i)}
            yield Prompt(text=text, metadata=meta)
            n += 1

    async def size(self) -> int | None:
        return self.limit
