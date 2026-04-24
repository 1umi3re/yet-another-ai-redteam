from __future__ import annotations
from importlib.metadata import entry_points
from typing import Any

GROUPS = ("targets", "datasets", "converters", "executors", "scorers", "scenarios")


class Registry:
    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    def _load(self, group: str) -> dict[str, Any]:
        if group in self._cache:
            return self._cache[group]
        eps = entry_points(group=f"airedteam.{group}")
        out: dict[str, Any] = {}
        for ep in eps:
            try:
                out[ep.name] = ep.load()
            except Exception as e:  # pragma: no cover
                out[ep.name] = e
        self._cache[group] = out
        return out

    def list(self, group: str) -> list[str]:
        assert group in GROUPS, group
        return sorted(self._load(group).keys())

    def get(self, group: str, name: str) -> Any:
        assert group in GROUPS, group
        item = self._load(group).get(name)
        if isinstance(item, Exception):
            raise item
        if item is None:
            raise KeyError(f"{group}/{name} not registered")
        return item

    def register(self, group: str, name: str, cls: Any) -> None:
        """Register a plugin class in-process (primarily for tests)."""
        assert group in GROUPS, group
        self._load(group)  # ensure group initialized
        self._cache[group][name] = cls


_default: Registry | None = None


def default_registry() -> Registry:
    global _default
    if _default is None:
        _default = Registry()
    return _default
