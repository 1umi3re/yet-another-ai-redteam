from __future__ import annotations

from typing import Any

from airedteam.builtins.converters.support.template_backed import PromptFramingTemplateConverter
from airedteam.core.prompt_framing_templates import (
    attack_method_template_asset_id,
    attack_method_template_defaults,
)
from airedteam.core.registry import default_registry

TARGET_RUNTIME_PARAM_KEYS = {
    "max_concurrency",
    "max_input_chars",
    "input_limit_unit",
}


def _instantiate(group: str, ref: dict, **extra: Any):
    plugin = ref.get("plugin")
    if not plugin:
        raise ValueError(f"{group} ref missing 'plugin': {ref}")
    params = dict(ref.get("params") or {})
    params.update(extra)
    cls = default_registry().get(group, plugin)
    return cls(**params)


def build_target(ref: dict):
    filtered = dict(ref)
    params = dict(filtered.get("params") or {})
    for key in TARGET_RUNTIME_PARAM_KEYS:
        params.pop(key, None)
    filtered["params"] = params
    return _instantiate("targets", filtered)


def build_dataset(ref: dict, *, blob_store=None):
    plugin = ref.get("plugin")
    params = dict(ref.get("params") or {})
    if plugin == "json_upload" and blob_store is not None and "blob_store" not in params:
        params["blob_store"] = blob_store
    cls = default_registry().get("datasets", plugin)
    return cls(**params)


def build_converter(ref: dict):
    plugin = ref.get("plugin")
    params = dict(ref.get("params") or {})
    if plugin and attack_method_template_asset_id(plugin) is not None and "template" in params:
        template = params.pop("template")
        variables = attack_method_template_defaults(plugin)
        variables.update(params)
        return PromptFramingTemplateConverter(
            method_name=plugin,
            template=template,
            variables=variables,
        )
    return _instantiate("converters", ref)


def build_executor(ref: dict):
    return _instantiate("executors", ref)


def build_scorer(ref: dict):
    return _instantiate("scorers", ref)
