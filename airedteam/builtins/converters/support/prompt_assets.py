from __future__ import annotations

from typing import Any


async def render_converter_prompt(
    prompt_assets: Any | None,
    asset_id: str,
    variables: dict[str, Any],
    fallback_template: str,
) -> str:
    if prompt_assets is None:
        return fallback_template.format(**{key: str(value) for key, value in variables.items()})
    rendered = await prompt_assets.render(asset_id, variables)
    return str(rendered["rendered_text"])
