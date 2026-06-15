from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from importlib import resources
from string import Formatter
from typing import Any

from sqlalchemy import delete, select, update

from airedteam.storage import models


@dataclass(frozen=True)
class PromptAsset:
    id: str
    version: int
    plugin: str
    purpose: str
    category: str
    variables: list[str]
    template: str
    source: str = "builtin"

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "plugin": self.plugin,
            "purpose": self.purpose,
            "category": self.category,
            "variables": self.variables,
            "template": self.template,
            "source": self.source,
            "is_custom": self.source == "custom",
        }


class PromptAssetService:
    def __init__(self, session_factory, blob_store) -> None:
        self._sf = session_factory
        self._blob = blob_store
        self._builtins = _load_builtins()

    async def list_assets(self) -> list[dict[str, Any]]:
        assets = list(self._builtins.values()) + await self._list_custom_assets()
        out: list[dict[str, Any]] = []
        for asset in sorted(assets, key=lambda a: a.id):
            item = asset.public()
            item["active_override"] = await self._active_override_public(asset.id)
            out.append(item)
        return out

    def list_builtin_assets(self) -> list[dict[str, Any]]:
        return [asset.public() for asset in sorted(self._builtins.values(), key=lambda a: a.id)]

    async def get_asset(self, asset_id: str) -> dict[str, Any]:
        asset = await self._get_asset(asset_id)
        item = asset.public()
        item["overrides"] = await self.list_overrides(asset_id)
        item["active_override"] = await self._active_override_public(asset_id)
        return item

    async def list_overrides(self, asset_id: str) -> list[dict[str, Any]]:
        await self._get_asset(asset_id)
        async with self._sf() as s:
            rows = (
                (
                    await s.execute(
                        select(models.PromptAssetOverride)
                        .where(models.PromptAssetOverride.asset_id == asset_id)
                        .order_by(models.PromptAssetOverride.created_at.desc())
                    )
                )
                .scalars()
                .all()
            )
            return [_override_public(row) for row in rows]

    async def create_override(
        self,
        asset_id: str,
        *,
        name: str,
        template: str,
        active: bool = False,
    ) -> dict[str, Any]:
        await self._validate_template(asset_id, template)
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
        self,
        override_id: str,
        *,
        name: str | None = None,
        template: str | None = None,
    ) -> dict[str, Any]:
        async with self._sf() as s:
            row = await s.get(models.PromptAssetOverride, override_id)
            if row is None:
                raise KeyError(override_id)
            if name is not None:
                row.name = name
            if template is not None:
                await self._validate_template(row.asset_id, template)
                row.template_text = template
            await s.commit()
            await s.refresh(row)
            return _override_public(row)

    async def set_active_override(
        self,
        asset_id: str,
        override_id: str | None,
    ) -> dict[str, Any] | None:
        await self._get_asset(asset_id)
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

    async def delete_override(self, override_id: str) -> None:
        async with self._sf() as s:
            row = await s.get(models.PromptAssetOverride, override_id)
            if row is None:
                raise KeyError(override_id)
            await s.delete(row)
            await s.commit()

    async def delete_asset(self, asset_id: str) -> None:
        if asset_id in self._builtins:
            raise ValueError("built-in prompt assets cannot be deleted")
        async with self._sf() as s:
            row = await s.get(models.PromptAssetCustom, asset_id)
            if row is None:
                raise KeyError(asset_id)
            await s.execute(delete(models.PromptAssetOverride).where(models.PromptAssetOverride.asset_id == asset_id))
            await s.delete(row)
            await s.commit()

    async def create_asset(
        self,
        *,
        asset_id: str,
        plugin: str,
        purpose: str,
        category: str | None = None,
        variables: list[str] | None,
        template: str,
        version: int = 1,
    ) -> dict[str, Any]:
        asset_id = asset_id.strip()
        plugin = plugin.strip() or "custom"
        purpose = purpose.strip() or "custom"
        category = _normalize_category(category, purpose=purpose, plugin=plugin, asset_id=asset_id)
        if not asset_id:
            raise ValueError("prompt asset id is required")
        if not re.fullmatch(r"[A-Za-z0-9_.:-]+", asset_id):
            raise ValueError("prompt asset id may only contain letters, numbers, underscore, dash, colon, and dot")
        if asset_id in self._builtins:
            raise ValueError(f"prompt asset already exists: {asset_id}")
        if not template.strip():
            raise ValueError("template is required")
        try:
            version = int(version)
        except (TypeError, ValueError):
            raise ValueError("version must be an integer") from None
        if version < 1:
            raise ValueError("version must be >= 1")

        fields = _template_fields(template)
        if purpose == "attack_template" and "prompt" not in fields:
            raise ValueError("attack templates must include {prompt}")
        normalized_vars = _normalize_variables(variables or [], fields)
        unknown = sorted(fields.difference(normalized_vars))
        if unknown:
            raise ValueError(f"template variables not declared: {', '.join(unknown)}")

        async with self._sf() as s:
            if await s.get(models.PromptAssetCustom, asset_id) is not None:
                raise ValueError(f"prompt asset already exists: {asset_id}")
            row = models.PromptAssetCustom(
                id=asset_id,
                version=version,
                plugin=plugin,
                purpose=purpose,
                category=category,
                variables_json=normalized_vars,
                template_text=template,
            )
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return _custom_asset(row).public()

    async def render(
        self,
        asset_id: str,
        variables: dict[str, Any],
        *,
        override_id: str | None = None,
        use_builtin: bool = False,
    ) -> dict[str, Any]:
        asset = await self._get_asset(asset_id)
        template = asset.template
        source = asset.source
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
            "category": asset.category,
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

    async def _get_asset(self, asset_id: str) -> PromptAsset:
        if asset_id in self._builtins:
            return self._builtins[asset_id]
        async with self._sf() as s:
            row = await s.get(models.PromptAssetCustom, asset_id)
            if row is None:
                raise KeyError(asset_id)
            return _custom_asset(row)

    async def _list_custom_assets(self) -> list[PromptAsset]:
        async with self._sf() as s:
            rows = (
                (await s.execute(select(models.PromptAssetCustom).order_by(models.PromptAssetCustom.id)))
                .scalars()
                .all()
            )
            return [_custom_asset(row) for row in rows]

    async def _validate_template(self, asset_id: str, template: str) -> None:
        asset = await self._get_asset(asset_id)
        fields = _template_fields(template)
        if asset.purpose == "attack_template" and "prompt" not in fields:
            raise ValueError(f"attack template {asset_id} must include {{prompt}}")
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
            return (
                await s.execute(
                    select(models.PromptAssetOverride)
                    .where(
                        models.PromptAssetOverride.asset_id == asset_id,
                        models.PromptAssetOverride.is_active.is_(True),
                    )
                    .order_by(models.PromptAssetOverride.updated_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()

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


def _custom_asset(row: models.PromptAssetCustom) -> PromptAsset:
    return PromptAsset(
        id=row.id,
        version=int(row.version),
        plugin=row.plugin,
        purpose=row.purpose,
        category=getattr(row, "category", None)
        or _derive_category(
            {
                "id": row.id,
                "plugin": row.plugin,
                "purpose": row.purpose,
            }
        ),
        variables=[str(v) for v in (row.variables_json or [])],
        template=row.template_text,
        source="custom",
    )


def _template_fields(template: str) -> set[str]:
    fields: set[str] = set()
    for _, name, _, _ in Formatter().parse(template):
        if name is not None and name != "":
            fields.add(name)
    invalid = sorted(v for v in fields if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", v))
    if invalid:
        raise ValueError(f"invalid prompt variable names: {', '.join(invalid)}")
    return fields


def _normalize_variables(variables: list[str], fields: set[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    source = variables or sorted(fields)
    for item in source:
        var = str(item).strip()
        if not var:
            continue
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", var):
            raise ValueError(f"invalid prompt variable name: {var}")
        if var not in seen:
            seen.add(var)
            out.append(var)
    return out


def _normalize_category(
    category: str | None,
    *,
    purpose: str,
    plugin: str,
    asset_id: str,
) -> str:
    value = str(category or "").strip()
    if value:
        return value[:200]
    return _derive_category({"id": asset_id, "purpose": purpose, "plugin": plugin})


def _derive_category(item: dict[str, Any]) -> str:
    asset_id = str(item.get("id") or "")
    purpose = str(item.get("purpose") or "")
    plugin = str(item.get("plugin") or "")
    executor_label = {
        "crescendo": "Crescendo",
        "pair": "PAIR",
        "jailbreak_iterative": "Jailbreak Iterative",
        "general_multi_turn": "General Multi Turn",
    }.get(plugin)
    if purpose == "attack_template":
        if asset_id.startswith("attack_method."):
            return f"Attack Methods / {plugin}" if plugin else "Attack Methods"
        if asset_id.startswith("attack_template.pyrit.arth_singh."):
            return "PyRIT / Arth Singh"
        if asset_id.startswith("attack_template.pyrit.pliny."):
            return "PyRIT / Pliny"
        if asset_id.startswith("attack_template.pyrit."):
            return "PyRIT / Classic"
        return "Built-in"
    if purpose == "converter_prompt":
        return "Converters"
    if executor_label and purpose in {
        "next_user_message",
        "turn_feedback",
        "refine_attack",
        "score_turn",
        "success_judgement",
    }:
        return f"Executors / {executor_label}"
    if purpose in {"next_user_message", "turn_feedback", "refine_attack"}:
        return f"Executors / {plugin}" if plugin else "Executors"
    if purpose in {"score_single_attempt", "score_conversation", "score_turn", "success_judgement"}:
        return "Judging"
    return plugin or "custom"


def _load_builtins() -> dict[str, PromptAsset]:
    package_files = resources.files("airedteam.builtins.prompt_assets")
    assets: dict[str, PromptAsset] = {}
    for resource in sorted(package_files.iterdir(), key=lambda path: path.name):
        if resource.name == "__init__.py" or not resource.name.endswith(".json"):
            continue
        data = json.loads(resource.read_text())
        for item in data:
            asset = PromptAsset(
                id=item["id"],
                version=int(item["version"]),
                plugin=item["plugin"],
                purpose=item["purpose"],
                category=str(item.get("category") or _derive_category(item)),
                variables=list(item["variables"]),
                template=item["template"],
            )
            if asset.id in assets:
                raise ValueError(f"duplicate built-in prompt asset id: {asset.id}")
            assets[asset.id] = asset
    return assets
