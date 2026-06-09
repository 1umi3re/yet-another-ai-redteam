from __future__ import annotations

import re
from collections import Counter
from typing import Any

from sqlalchemy import select

from airedteam.core.attack_method_categories import (
    DEFAULT_ATTACK_METHOD_CATEGORIES,
    UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID,
    default_attack_method_category_for,
    fallback_category_meta,
)
from airedteam.storage import models

EXECUTOR_KINDS = {"executor", "converter_method"}


class AttackMethodCategoryService:
    def __init__(self, session_factory) -> None:
        self._sf = session_factory

    async def ensure_defaults(
        self,
        *,
        native_executors: list[str],
        converter_methods: list[str],
        technical_categories: dict[str, str],
    ) -> None:
        async with self._sf() as s:
            existing_categories = set(
                (
                    await s.execute(select(models.AttackMethodCategory.id))
                ).scalars()
            )
            for category in DEFAULT_ATTACK_METHOD_CATEGORIES:
                if category.id in existing_categories:
                    continue
                s.add(
                    models.AttackMethodCategory(
                        id=category.id,
                        name=category.name,
                        alias=category.alias,
                        category_type=category.type,
                        description=category.description,
                        display_order=category.display_order,
                        is_builtin=True,
                    )
                )

            existing_mappings = {
                (row.executor_kind, row.executor_name)
                for row in (
                    await s.execute(
                        select(
                            models.ExecutorMethodCategory.executor_kind,
                            models.ExecutorMethodCategory.executor_name,
                        )
                    )
                ).all()
            }
            for executor_kind, names in (
                ("executor", native_executors),
                ("converter_method", converter_methods),
            ):
                for name in names:
                    key = (executor_kind, name)
                    if key in existing_mappings:
                        continue
                    category_id = default_attack_method_category_for(executor_kind, name)
                    if category_id == UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID:
                        continue
                    s.add(
                        models.ExecutorMethodCategory(
                            executor_kind=executor_kind,
                            executor_name=name,
                            category_id=category_id,
                            technical_category=technical_categories.get(name)
                            if executor_kind == "converter_method"
                            else "executor",
                            is_builtin=True,
                        )
                    )
            await s.commit()

    async def list_catalog(self) -> dict[str, list[dict[str, Any]]]:
        async with self._sf() as s:
            categories = (
                (
                    await s.execute(
                        select(models.AttackMethodCategory).order_by(
                            models.AttackMethodCategory.display_order,
                            models.AttackMethodCategory.id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            mappings = (
                (
                    await s.execute(
                        select(models.ExecutorMethodCategory).order_by(
                            models.ExecutorMethodCategory.executor_kind,
                            models.ExecutorMethodCategory.executor_name,
                        )
                    )
                )
                .scalars()
                .all()
            )
        counts = Counter(mapping.category_id for mapping in mappings)
        return {
            "categories": [_category_public(category, counts[category.id]) for category in categories],
            "mappings": [_mapping_public(mapping) for mapping in mappings],
        }

    async def create_category(
        self,
        *,
        category_id: str,
        name: str,
        alias: str,
        type: str,
        description: str | None,
        display_order: int,
    ) -> dict[str, Any]:
        category_id = _normalize_category_id(category_id)
        name = name.strip()
        if not name:
            raise ValueError("category name is required")
        async with self._sf() as s:
            if await s.get(models.AttackMethodCategory, category_id) is not None:
                raise ValueError(f"attack method category already exists: {category_id}")
            row = models.AttackMethodCategory(
                id=category_id,
                name=name,
                alias=alias.strip(),
                category_type=type.strip(),
                description=_optional_text(description),
                display_order=int(display_order),
                is_builtin=False,
            )
            s.add(row)
            await s.commit()
            await s.refresh(row)
            return _category_public(row, 0)

    async def update_category(
        self,
        category_id: str,
        *,
        name: str | None = None,
        alias: str | None = None,
        type: str | None = None,
        description: str | None = None,
        display_order: int | None = None,
    ) -> dict[str, Any]:
        async with self._sf() as s:
            row = await s.get(models.AttackMethodCategory, category_id)
            if row is None:
                raise KeyError(category_id)
            if name is not None:
                name = name.strip()
                if not name:
                    raise ValueError("category name is required")
                row.name = name
            if alias is not None:
                row.alias = alias.strip()
            if type is not None:
                row.category_type = type.strip()
            if description is not None:
                row.description = _optional_text(description)
            if display_order is not None:
                row.display_order = int(display_order)
            await s.commit()
            await s.refresh(row)
            count = len(
                (
                    await s.execute(
                        select(models.ExecutorMethodCategory).where(
                            models.ExecutorMethodCategory.category_id == row.id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            return _category_public(row, count)

    async def delete_category(self, category_id: str) -> None:
        async with self._sf() as s:
            row = await s.get(models.AttackMethodCategory, category_id)
            if row is None:
                raise KeyError(category_id)
            mappings = (
                (
                    await s.execute(
                        select(models.ExecutorMethodCategory).where(
                            models.ExecutorMethodCategory.category_id == category_id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            if mappings:
                raise ValueError("category still has mappings")
            await s.delete(row)
            await s.commit()

    async def upsert_mapping(
        self,
        executor_kind: str,
        executor_name: str,
        *,
        category_id: str,
        technical_category: str | None = None,
    ) -> dict[str, Any]:
        executor_kind = executor_kind.strip()
        executor_name = executor_name.strip()
        if executor_kind not in EXECUTOR_KINDS:
            raise ValueError("executor kind must be executor or converter_method")
        if not executor_name:
            raise ValueError("executor name is required")
        async with self._sf() as s:
            if await s.get(models.AttackMethodCategory, category_id) is None:
                raise KeyError(category_id)
            row = await s.get(models.ExecutorMethodCategory, (executor_kind, executor_name))
            if row is None:
                row = models.ExecutorMethodCategory(
                    executor_kind=executor_kind,
                    executor_name=executor_name,
                    category_id=category_id,
                    technical_category=_optional_text(technical_category),
                    is_builtin=False,
                )
                s.add(row)
            else:
                row.category_id = category_id
                row.technical_category = _optional_text(technical_category)
                row.is_builtin = False
            await s.commit()
            await s.refresh(row)
            return _mapping_public(row)


def category_meta_from_catalog(catalog: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return {category["id"]: category for category in catalog["categories"]}


def attack_categories_from_catalog(
    catalog: dict[str, list[dict[str, Any]]],
    *,
    native_executors: list[str],
    converter_methods: list[str],
) -> dict[str, str]:
    mappings = {
        (mapping["executor_kind"], mapping["executor_name"]): mapping["category_id"]
        for mapping in catalog["mappings"]
    }
    out: dict[str, str] = {}
    for name in native_executors:
        out[name] = mappings.get(
            ("executor", name),
            default_attack_method_category_for("executor", name),
        )
    for name in converter_methods:
        out[name] = mappings.get(
            ("converter_method", name),
            default_attack_method_category_for("converter_method", name),
        )
    return out


def technical_categories_from_catalog(
    catalog: dict[str, list[dict[str, Any]]],
    *,
    native_executors: list[str],
    converter_methods: list[str],
    default_technical_categories: dict[str, str],
) -> dict[str, str]:
    mappings = {
        (mapping["executor_kind"], mapping["executor_name"]): mapping.get("technical_category")
        for mapping in catalog["mappings"]
    }
    out: dict[str, str] = {}
    for name in native_executors:
        out[name] = mappings.get(("executor", name)) or "executor"
    for name in converter_methods:
        out[name] = mappings.get(("converter_method", name)) or default_technical_categories.get(name, "other")
    return out


def meta_with_fallback(
    meta: dict[str, dict[str, Any]],
    attack_categories: dict[str, str],
) -> dict[str, dict[str, Any]]:
    if UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID not in set(attack_categories.values()):
        return meta
    return {**meta, UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID: fallback_category_meta()}


def _category_public(row: models.AttackMethodCategory, mapped_count: int) -> dict[str, Any]:
    return {
        "id": row.id,
        "name": row.name,
        "alias": row.alias,
        "type": row.category_type,
        "description": row.description,
        "display_order": row.display_order,
        "is_builtin": row.is_builtin,
        "mapped_count": mapped_count,
    }


def _mapping_public(row: models.ExecutorMethodCategory) -> dict[str, Any]:
    return {
        "executor_kind": row.executor_kind,
        "executor_name": row.executor_name,
        "category_id": row.category_id,
        "technical_category": row.technical_category,
        "is_builtin": row.is_builtin,
    }


def _normalize_category_id(category_id: str) -> str:
    category_id = category_id.strip()
    if not category_id:
        raise ValueError("category id is required")
    if not re.fullmatch(r"[a-z0-9_:-]+", category_id):
        raise ValueError("category id may only contain lowercase letters, numbers, underscore, dash, and colon")
    return category_id


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
