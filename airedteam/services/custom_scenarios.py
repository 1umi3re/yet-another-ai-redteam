from __future__ import annotations

from copy import deepcopy
from typing import Any

from sqlalchemy import select

from airedteam.storage.models import CustomScenario

CUSTOM_SCENARIO_PREFIX = "custom:"

_TEMPLATE_KEYS = {
    "version",
    "executors",
    "executor",
    "converters",
    "scorers",
    "scorer",
    "sampling",
    "timeout_seconds",
}


def public_custom_scenario_id(scenario_id: str) -> str:
    return f"{CUSTOM_SCENARIO_PREFIX}{scenario_id}"


def internal_custom_scenario_id(public_id: str) -> str | None:
    if not public_id.startswith(CUSTOM_SCENARIO_PREFIX):
        return None
    value = public_id.removeprefix(CUSTOM_SCENARIO_PREFIX)
    return value or None


def _has_items(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def _sanitize_template(template: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(template, dict):
        raise ValueError("custom scenario template must be an object")
    clean = {key: deepcopy(template[key]) for key in _TEMPLATE_KEYS if key in template}
    clean.setdefault("version", 2)

    has_attack_method = (
        _has_items(clean.get("executors"))
        or isinstance(clean.get("executor"), dict)
        or _has_items(clean.get("converters"))
    )
    if not has_attack_method:
        raise ValueError("custom scenario requires at least one attack method")

    has_scorer = _has_items(clean.get("scorers")) or isinstance(clean.get("scorer"), dict)
    if not has_scorer:
        raise ValueError("custom scenario requires at least one scorer")

    return clean


def _scenario_out(row: CustomScenario) -> dict[str, Any]:
    return {
        "id": public_custom_scenario_id(row.id),
        "custom_id": row.id,
        "title": row.name,
        "description": row.description or "",
        "tags": list(row.tags_json or []),
        "level": "custom",
        "source": "custom",
        "requirements": [],
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


class CustomScenarioService:
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    async def create(
        self,
        *,
        name: str,
        description: str = "",
        tags: list[str] | None = None,
        template: dict[str, Any],
    ) -> dict[str, Any]:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("custom scenario name is required")
        clean_tags = [tag.strip() for tag in tags or [] if tag.strip()]
        clean_template = _sanitize_template(template)
        async with self._session_factory() as session:
            row = CustomScenario(
                name=clean_name,
                description=description.strip(),
                tags_json=clean_tags,
                template_json=clean_template,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _scenario_out(row)

    async def list(self) -> list[dict[str, Any]]:
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(CustomScenario).order_by(CustomScenario.created_at.desc(), CustomScenario.name)
                )
            ).scalars().all()
            return [_scenario_out(row) for row in rows]

    async def render_runspec(
        self,
        *,
        public_id: str,
        target_config_id: str,
        dataset_config_id: str,
    ) -> dict[str, Any]:
        scenario_id = internal_custom_scenario_id(public_id)
        if scenario_id is None:
            raise KeyError(public_id)
        async with self._session_factory() as session:
            row = await session.get(CustomScenario, scenario_id)
            if row is None:
                raise KeyError(public_id)
            spec = deepcopy(row.template_json or {})
            spec["version"] = spec.get("version", 2)
            spec["name"] = row.name
            spec["scenario"] = public_custom_scenario_id(row.id)
            spec["targets"] = [{"config_id": target_config_id}]
            spec["dataset"] = {"config_id": dataset_config_id}
            return spec
