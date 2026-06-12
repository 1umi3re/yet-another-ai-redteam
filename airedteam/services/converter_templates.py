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
    if params.get("attack_template_asset_id"):
        asset_id = str(params.pop("attack_template_asset_id"))
    elif converter_plugin != "template_jailbreak":
        asset_id = attack_method_template_asset_id(converter_plugin)

    if not asset_id:
        return

    asset = await prompt_assets.get_asset(asset_id)
    if asset.get("purpose") != "attack_template":
        raise ValueError(f"prompt asset is not an attack template: {asset_id}")
    active_override = asset.get("active_override")
    params["template"] = (
        active_override.get("template")
        if isinstance(active_override, dict) and active_override.get("template")
        else asset["template"]
    )
