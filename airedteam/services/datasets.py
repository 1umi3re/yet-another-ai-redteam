from __future__ import annotations
import json
import uuid
from sqlalchemy import select
from airedteam.storage.models import DatasetMeta
from airedteam.storage.blobs import BlobStore


class DatasetService:
    def __init__(self, session_factory, blob_store: BlobStore) -> None:
        self._sf = session_factory
        self._blob = blob_store

    async def create_json_upload(self, *, name: str, file_bytes: bytes) -> DatasetMeta:
        raw = json.loads(file_bytes.decode())
        items = raw.get("items") if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            raise ValueError("dataset must be a JSON array or {items: [...]}")
        key = f"datasets/{uuid.uuid4()}.json"
        await self._blob.put(key, file_bytes)
        async with self._sf() as s:
            row = DatasetMeta(name=name, plugin="json_upload",
                              params_json={"blob_path": key},
                              blob_path=key, item_count=len(items))
            s.add(row); await s.commit(); await s.refresh(row); return row

    async def create_hf(self, *, name: str, repo: str, split: str = "train", prompt_field: str = "prompt", limit: int | None = None) -> DatasetMeta:
        async with self._sf() as s:
            row = DatasetMeta(name=name, plugin="hf",
                              params_json={"repo": repo, "split": split, "prompt_field": prompt_field, "limit": limit},
                              blob_path=None, item_count=limit)
            s.add(row); await s.commit(); await s.refresh(row); return row

    async def list(self) -> list[DatasetMeta]:
        async with self._sf() as s:
            r = await s.execute(select(DatasetMeta).order_by(DatasetMeta.created_at.desc()))
            return list(r.scalars().all())

    async def get(self, ds_id: str) -> DatasetMeta | None:
        async with self._sf() as s:
            return await s.get(DatasetMeta, ds_id)

    async def resolve_for_runtime(self, ds_id: str) -> dict:
        ds = await self.get(ds_id)
        if ds is None:
            raise KeyError(ds_id)
        return {"plugin": ds.plugin, "params": dict(ds.params_json or {})}
