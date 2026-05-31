from __future__ import annotations

import json
from collections.abc import AsyncIterator

from airedteam.core.types import Prompt
from airedteam.storage.blobs import BlobStore


class JsonUploadDataset:
    name = "json_upload"

    def __init__(
        self, *, blob_store: BlobStore, blob_path: str, prompt_field: str = "prompt", id_field: str = "id"
    ) -> None:
        self._blob = blob_store
        self._path = blob_path
        self._prompt_field = prompt_field
        self._id_field = id_field
        self._cache: list[Prompt] | None = None

    async def _load(self) -> list[Prompt]:
        if self._cache is not None:
            return self._cache
        raw = json.loads((await self._blob.get(self._path)).decode())
        items_raw = raw.get("items") if isinstance(raw, dict) else raw
        out: list[Prompt] = []
        for i, it in enumerate(items_raw):
            if isinstance(it, str):
                out.append(Prompt(text=it, metadata={"id": str(i)}))
            else:
                out.append(
                    Prompt(
                        text=it[self._prompt_field],
                        metadata={
                            "id": str(it.get(self._id_field, i)),
                            **{k: v for k, v in it.items() if k != self._prompt_field},
                        },
                    )
                )
        self._cache = out
        return out

    async def __aiter__(self) -> AsyncIterator[Prompt]:
        for p in await self._load():
            yield p

    async def size(self) -> int | None:
        return len(await self._load())
