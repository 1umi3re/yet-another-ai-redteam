from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib import resources
from string import Formatter
from typing import Any

from sqlalchemy import select, update

from airedteam.storage import models


@dataclass(frozen=True)
class PromptAsset:
    id: str
    version: int
    plugin: str
    purpose: str
    variables: list[str]
    template: str

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "plugin": self.plugin,
            "purpose": self.purpose,
            "variables": self.variables,
            "template": self.template,
        }


class PromptAssetService:
    def __init__(self, session_factory, blob_store) -> None:
        self._sf = session_factory
        self._blob = blob_store
        self._builtins = _load_builtins()

    async def list_assets(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for asset in sorted(self._builtins.values(), key=lambda a: a.id):
            item = asset.public()
            item["active_override"] = await self._active_override_public(asset.id)
            out.append(item)
        return out

    async def get_asset(self, asset_id: str) -> dict[str, Any]:
        asset = self._get_builtin(asset_id)
        item = asset.public()
        item["overrides"] = await self.list_overrides(asset_id)
        item["active_override"] = await self._active_override_public(asset_id)
        return item

    async def list_overrides(self, asset_id: str) -> list[dict[str, Any]]:
        self._get_builtin(asset_id)
        async with self._sf() as s:
            rows = (await s.execute(
                select(models.PromptAssetOverride)
                .where(models.PromptAssetOverride.asset_id == asset_id)
                .order_by(models.PromptAssetOverride.created_at.desc())
            )).scalars().all()
            return [_override_public(row) for row in rows]

    async def create_override(
        self, asset_id: str, *, name: str, template: str, active: bool = False,
    ) -> dict[str, Any]:
        self._validate_template(asset_id, template)
        async with self._sf() as s:
            if active:
                await s.execute(
                    update(models.PromptAssetOverride)
                    .where(models.PromptAssetOverride.asset_id == asset_id)
                    .values(is_active=False)
                )
            row = models.PromptAssetOverride(
                asset_id=asset_id,
                name=name,
                template_text=template,
                is_active=active,
            )
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return _override_public(row)

    async def update_override(
        self, override_id: str, *, name: str | None = None, template: str | None = None,
    ) -> dict[str, Any]:
        async with self._sf() as s:
            row = await s.get(models.PromptAssetOverride, override_id)
            if row is None:
                raise KeyError(override_id)
            if name is not None:
                row.name = name
            if template is not None:
                self._validate_template(row.asset_id, template)
                row.template_text = template
            await s.commit()
            await s.refresh(row)
            return _override_public(row)

    async def set_active_override(self, asset_id: str, override_id: str | None) -> dict[str, Any] | None:
        self._get_builtin(asset_id)
        async with self._sf() as s:
            if override_id is not None:
                row = await s.get(models.PromptAssetOverride, override_id)
                if row is None or row.asset_id != asset_id:
                    raise KeyError(override_id)
            await s.execute(
                update(models.PromptAssetOverride)
                .where(models.PromptAssetOverride.asset_id == asset_id)
                .values(is_active=False)
            )
            if override_id is None:
                await s.commit()
                return None
            await s.execute(
                update(models.PromptAssetOverride)
                .where(models.PromptAssetOverride.id == override_id)
                .values(is_active=True)
            )
            await s.commit()
            row = await s.get(models.PromptAssetOverride, override_id)
            return _override_public(row)

    async def render(
        self,
        asset_id: str,
        variables: dict[str, Any],
        *,
        override_id: str | None = None,
        use_builtin: bool = False,
    ) -> dict[str, Any]:
        asset = self._get_builtin(asset_id)
        template = asset.template
        source = "builtin"
        selected_override_id: str | None = None

        if override_id is not None:
            row = await self._get_override(override_id, asset_id)
            template = row.template_text
            source = "override"
            selected_override_id = row.id
        elif not use_builtin:
            row = await self._active_override(asset_id)
            if row is not None:
                template = row.template_text
                source = "override"
                selected_override_id = row.id

        missing = [v for v in asset.variables if v not in variables]
        if missing:
            raise ValueError(f"missing prompt variables for {asset_id}: {', '.join(missing)}")
        rendered = template.format(**{k: str(v) for k, v in variables.items()})
        digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        return {
            "asset_id": asset.id,
            "version": asset.version,
            "plugin": asset.plugin,
            "purpose": asset.purpose,
            "source": source,
            "override_id": selected_override_id,
            "variables": {k: str(variables[k]) for k in asset.variables if k in variables},
            "rendered_text": rendered,
            "sha256": digest,
        }

    async def write_snapshot(self, run_id: str, object_id: str, snapshot: dict[str, Any]) -> str:
        key = f"runs/{run_id}/prompt-snapshots/{object_id}.json"
        await self._blob.put(key, json.dumps(snapshot, ensure_ascii=False).encode("utf-8"))
        return key

    def _get_builtin(self, asset_id: str) -> PromptAsset:
        try:
            return self._builtins[asset_id]
        except KeyError:
            raise KeyError(asset_id)

    def _validate_template(self, asset_id: str, template: str) -> None:
        asset = self._get_builtin(asset_id)
        fields = {
            name for _, name, _, _ in Formatter().parse(template)
            if name is not None and name != ""
        }
        unknown = sorted(fields.difference(asset.variables))
        if unknown:
            raise ValueError(f"unknown prompt variables for {asset_id}: {', '.join(unknown)}")

    async def _get_override(self, override_id: str, asset_id: str):
        async with self._sf() as s:
            row = await s.get(models.PromptAssetOverride, override_id)
            if row is None or row.asset_id != asset_id:
                raise KeyError(override_id)
            return row

    async def _active_override(self, asset_id: str):
        async with self._sf() as s:
            return (await s.execute(
                select(models.PromptAssetOverride)
                .where(
                    models.PromptAssetOverride.asset_id == asset_id,
                    models.PromptAssetOverride.is_active.is_(True),
                )
                .order_by(models.PromptAssetOverride.updated_at.desc())
                .limit(1)
            )).scalar_one_or_none()

    async def _active_override_public(self, asset_id: str) -> dict[str, Any] | None:
        row = await self._active_override(asset_id)
        return _override_public(row) if row is not None else None


def _override_public(row: models.PromptAssetOverride) -> dict[str, Any]:
    return {
        "id": row.id,
        "asset_id": row.asset_id,
        "name": row.name,
        "template": row.template_text,
        "is_active": row.is_active,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _load_builtins() -> dict[str, PromptAsset]:
    raw = resources.files("airedteam.builtins.prompt_assets").joinpath("assets.json").read_text()
    data = json.loads(raw)
    return {
        item["id"]: PromptAsset(
            id=item["id"],
            version=int(item["version"]),
            plugin=item["plugin"],
            purpose=item["purpose"],
            variables=list(item["variables"]),
            template=item["template"],
        )
        for item in data
    }
