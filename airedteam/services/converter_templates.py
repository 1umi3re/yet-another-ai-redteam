from __future__ import annotations

from typing import Any

from airedteam.core.prompt_framing_templates import attack_method_template_asset_id


async def resolve_converter_attack_template(
    prompt_assets,
    *,
    converter_plugin: str | None,
    params: dict[str, Any],
) -> None:
    if prompt_assets is None or not converter_plugin:
        return

    asset_id: str | None = None
    override_id = params.pop("attack_template_override_id", None)
    use_builtin = _truthy(params.pop("attack_template_use_builtin", False))
    if params.get("attack_template_asset_id"):
        asset_id = str(params.pop("attack_template_asset_id"))
    elif converter_plugin != "template_jailbreak":
        asset_id = attack_method_template_asset_id(converter_plugin)

    if not asset_id:
        return

    asset = await prompt_assets.get_asset(asset_id)
    if asset.get("purpose") != "attack_template":
        raise ValueError(f"prompt asset is not an attack template: {asset_id}")
    if override_id:
        override = next(
            (item for item in asset.get("overrides") or [] if item.get("id") == str(override_id)),
            None,
        )
        if override is None:
            raise ValueError(f"prompt asset override not found for {asset_id}: {override_id}")
        params["template"] = override["template"]
        return
    active_override = None if use_builtin else asset.get("active_override")
    params["template"] = (
        active_override.get("template")
        if isinstance(active_override, dict) and active_override.get("template")
        else asset["template"]
    )


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
