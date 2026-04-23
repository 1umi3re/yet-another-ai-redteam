from __future__ import annotations
from typing import Any
from airedteam.core.registry import default_registry


def _instantiate(group: str, ref: dict, **extra: Any):
    plugin = ref.get("plugin")
    if not plugin:
        raise ValueError(f"{group} ref missing 'plugin': {ref}")
    params = dict(ref.get("params") or {})
    params.update(extra)
    cls = default_registry().get(group, plugin)
    return cls(**params)


def build_target(ref: dict):
    return _instantiate("targets", ref)


def build_dataset(ref: dict, *, blob_store=None):
    plugin = ref.get("plugin")
    params = dict(ref.get("params") or {})
    if plugin == "json_upload" and blob_store is not None and "blob_store" not in params:
        params["blob_store"] = blob_store
    cls = default_registry().get("datasets", plugin)
    return cls(**params)


def build_converter(ref: dict):
    return _instantiate("converters", ref)


def build_executor(ref: dict):
    return _instantiate("executors", ref)


def build_scorer(ref: dict):
    return _instantiate("scorers", ref)
