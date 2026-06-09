from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import func, select

from airedteam.core.language import detect_prompt_language, normalize_language
from airedteam.engine.factory import build_dataset
from airedteam.storage.blobs import BlobStore
from airedteam.storage.models import DatasetMeta, DatasetVersion


def _extract_items(raw: Any) -> list[Any]:
    items = raw.get("items") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise ValueError("dataset must be a JSON array or {items: [...]}")
    for index, item in enumerate(items):
        if isinstance(item, str):
            continue
        if not isinstance(item, dict):
            raise ValueError(f"dataset item {index} must be a string or object")
        if "prompt" not in item or not str(item["prompt"]).strip():
            raise ValueError(f"dataset item {index} must include a non-empty prompt field")
    return items


def _items_bytes(items: list[Any]) -> bytes:
    return json.dumps({"items": items}, ensure_ascii=False, indent=2).encode("utf-8")


def _item_dict(item: Any, index: int) -> dict[str, Any]:
    if isinstance(item, str):
        return {"id": str(index), "prompt": item}
    return dict(item)


def _ensure_item_language(item: dict[str, Any]) -> bool:
    language = normalize_language(item.get("language"))
    if language is not None:
        changed = language != item.get("language")
        item["language"] = language
        return changed
    item["language"] = detect_prompt_language(str(item.get("prompt", "")))
    return True


def _version_public(row: DatasetVersion, current_version: int | None) -> dict:
    return {
        "id": row.id,
        "dataset_id": row.dataset_id,
        "version": row.version,
        "item_count": row.item_count,
        "note": row.note,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "is_current": row.version == current_version,
    }


class DatasetService:
    def __init__(self, session_factory, blob_store: BlobStore) -> None:
        self._sf = session_factory
        self._blob = blob_store

    async def create_json_upload(self, *, name: str, file_bytes: bytes) -> DatasetMeta:
        items = _extract_items(json.loads(file_bytes.decode()))
        key = f"datasets/{uuid.uuid4()}.json"
        await self._blob.put(key, _items_bytes(items))
        async with self._sf() as s:
            row = DatasetMeta(
                name=name,
                plugin="json_upload",
                params_json={"blob_path": key},
                blob_path=key,
                item_count=len(items),
                current_version=1,
            )
            s.add(row)
            await s.flush()
            s.add(
                DatasetVersion(
                    dataset_id=row.id,
                    version=1,
                    blob_path=key,
                    item_count=len(items),
                    note="Initial upload",
                )
            )
            await s.commit()
            await s.refresh(row)
            return row

    async def create_hf(
        self, *, name: str, repo: str, split: str = "train", prompt_field: str = "prompt", limit: int | None = None
    ) -> DatasetMeta:
        async with self._sf() as s:
            row = DatasetMeta(
                name=name,
                plugin="hf",
                params_json={"repo": repo, "split": split, "prompt_field": prompt_field, "limit": limit},
                blob_path=None,
                item_count=limit,
            )
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return row

    async def list(self) -> list[DatasetMeta]:
        async with self._sf() as s:
            r = await s.execute(select(DatasetMeta).order_by(DatasetMeta.created_at.desc()))
            return list(r.scalars().all())

    async def get(self, ds_id: str) -> DatasetMeta | None:
        async with self._sf() as s:
            return await s.get(DatasetMeta, ds_id)

    async def content(self, ds_id: str) -> dict:
        ds = await self.get(ds_id)
        if ds is None:
            raise KeyError(ds_id)
        if ds.plugin != "json_upload" or not ds.blob_path:
            raise ValueError("only uploaded JSON datasets can be edited")
        raw = json.loads((await self._blob.get(ds.blob_path)).decode("utf-8"))
        items = _extract_items(raw)
        return {
            "id": ds.id,
            "name": ds.name,
            "plugin": ds.plugin,
            "version": getattr(ds, "current_version", None) or 1,
            "item_count": len(items),
            "items": items,
        }

    async def update_items(
        self,
        ds_id: str,
        *,
        items: list[Any],
        note: str | None = None,
    ) -> DatasetMeta:
        normalized_items = _extract_items(items)
        async with self._sf() as s:
            ds = await s.get(DatasetMeta, ds_id)
            if ds is None:
                raise KeyError(ds_id)
            if ds.plugin != "json_upload":
                raise ValueError("only uploaded JSON datasets can be edited")
            max_version = (
                await s.execute(select(func.max(DatasetVersion.version)).where(DatasetVersion.dataset_id == ds_id))
            ).scalar_one()
            next_version = int(max_version or getattr(ds, "current_version", 1) or 1) + 1
            key = f"datasets/{uuid.uuid4()}.json"
            await self._blob.put(key, _items_bytes(normalized_items))
            ds.blob_path = key
            ds.params_json = {**dict(ds.params_json or {}), "blob_path": key}
            ds.item_count = len(normalized_items)
            ds.current_version = next_version
            s.add(
                DatasetVersion(
                    dataset_id=ds.id,
                    version=next_version,
                    blob_path=key,
                    item_count=len(normalized_items),
                    note=(note or "").strip() or None,
                )
            )
            await s.commit()
            await s.refresh(ds)
            return ds

    async def ensure_languages_for_run(self, ds_id: str) -> DatasetMeta:
        ds = await self.get(ds_id)
        if ds is None:
            raise KeyError(ds_id)
        if ds.plugin == "json_upload" and ds.blob_path:
            return await self._ensure_json_upload_languages(ds)
        return await self._create_language_snapshot(ds)

    async def _ensure_json_upload_languages(self, ds: DatasetMeta) -> DatasetMeta:
        raw = json.loads((await self._blob.get(ds.blob_path)).decode("utf-8"))
        items = _extract_items(raw)
        normalized_items: list[dict[str, Any]] = []
        changed = False
        for index, item in enumerate(items):
            item_dict = _item_dict(item, index)
            changed = _ensure_item_language(item_dict) or changed
            changed = not isinstance(item, dict) or item_dict != item or changed
            normalized_items.append(item_dict)
        if not changed:
            return ds
        return await self.update_items(
            ds.id,
            items=normalized_items,
            note="Auto-detected dataset item languages",
        )

    async def _create_language_snapshot(self, ds: DatasetMeta) -> DatasetMeta:
        ds_ref = await self.resolve_for_runtime(ds.id)
        dataset = build_dataset(ds_ref, blob_store=self._blob)
        items: list[dict[str, Any]] = []
        index = 0
        async for prompt in dataset:
            item = {"prompt": prompt.text, **dict(prompt.metadata)}
            item.setdefault("id", str(index))
            _ensure_item_language(item)
            items.append(item)
            index += 1
        key = f"datasets/{uuid.uuid4()}.json"
        await self._blob.put(key, _items_bytes(items))
        async with self._sf() as s:
            row = DatasetMeta(
                name=f"{ds.name} language snapshot {uuid.uuid4().hex[:8]}",
                plugin="json_upload",
                params_json={
                    "blob_path": key,
                    "source_dataset_id": ds.id,
                    "source_dataset_plugin": ds.plugin,
                },
                blob_path=key,
                item_count=len(items),
                current_version=1,
            )
            s.add(row)
            await s.flush()
            s.add(
                DatasetVersion(
                    dataset_id=row.id,
                    version=1,
                    blob_path=key,
                    item_count=len(items),
                    note=f"Language snapshot of {ds.name}",
                )
            )
            await s.commit()
            await s.refresh(row)
            return row

    async def list_versions(self, ds_id: str) -> list[dict]:
        ds = await self.get(ds_id)
        if ds is None:
            raise KeyError(ds_id)
        if ds.plugin != "json_upload":
            return []
        async with self._sf() as s:
            rows = (
                (
                    await s.execute(
                        select(DatasetVersion)
                        .where(DatasetVersion.dataset_id == ds_id)
                        .order_by(DatasetVersion.version.desc())
                    )
                )
                .scalars()
                .all()
            )
        current_version = getattr(ds, "current_version", None) or 1
        if not rows and ds.blob_path:
            return [
                {
                    "id": None,
                    "dataset_id": ds.id,
                    "version": current_version,
                    "item_count": ds.item_count,
                    "note": "Current dataset",
                    "created_at": ds.created_at.isoformat() if ds.created_at else None,
                    "is_current": True,
                }
            ]
        return [_version_public(row, current_version) for row in rows]

    async def restore_version(self, ds_id: str, version: int) -> DatasetMeta:
        async with self._sf() as s:
            ds = await s.get(DatasetMeta, ds_id)
            if ds is None:
                raise KeyError(ds_id)
            if ds.plugin != "json_upload":
                raise ValueError("only uploaded JSON datasets can restore versions")
            row = (
                await s.execute(
                    select(DatasetVersion).where(
                        DatasetVersion.dataset_id == ds_id,
                        DatasetVersion.version == version,
                    )
                )
            ).scalar_one_or_none()
            if row is None:
                if version == (getattr(ds, "current_version", None) or 1) and ds.blob_path:
                    return ds
                raise KeyError(str(version))
            ds.blob_path = row.blob_path
            ds.params_json = {**dict(ds.params_json or {}), "blob_path": row.blob_path}
            ds.item_count = row.item_count
            ds.current_version = row.version
            await s.commit()
            await s.refresh(ds)
            return ds

    async def resolve_for_runtime(self, ds_id: str) -> dict:
        ds = await self.get(ds_id)
        if ds is None:
            raise KeyError(ds_id)
        return {"plugin": ds.plugin, "params": dict(ds.params_json or {})}

    async def list_items(
        self,
        ds_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
        q: str | None = None,
    ) -> dict:
        ds_ref = await self.resolve_for_runtime(ds_id)
        dataset = build_dataset(ds_ref, blob_store=self._blob)
        matches: list[dict] = []
        q_norm = q.lower().strip() if q else ""
        seen = 0
        async for prompt in dataset:
            item = {
                "id": str(prompt.metadata.get("id", seen)),
                "text": prompt.text,
                "metadata": dict(prompt.metadata),
            }
            seen += 1
            if q_norm and q_norm not in item["text"].lower() and q_norm not in item["id"].lower():
                continue
            matches.append(item)
        items = matches[offset : offset + limit]
        return {
            "items": items,
            "total_returned": len(items),
            "total": len(matches),
            "offset": offset,
            "limit": limit,
            "has_more": offset + len(items) < len(matches),
        }
