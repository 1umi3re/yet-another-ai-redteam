from __future__ import annotations
import asyncio
from pathlib import Path
from typing import Protocol


class BlobStore(Protocol):
    async def put(self, key: str, data: bytes) -> str: ...
    async def get(self, key: str) -> bytes: ...
    async def exists(self, key: str) -> bool: ...


class LocalBlobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, data: bytes) -> str:
        target = self.root / key
        target.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(target.write_bytes, data)
        return key

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread((self.root / key).read_bytes)

    async def exists(self, key: str) -> bool:
        return (self.root / key).exists()
