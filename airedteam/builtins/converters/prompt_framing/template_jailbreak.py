from __future__ import annotations

from airedteam.core.types import Prompt


class TemplateJailbreakConverter:
    """Inject the prompt into a configurable text jailbreak template."""

    name = "template_jailbreak"

    def __init__(
        self,
        *,
        template: str = "{prompt}",
        attack_template_asset_id: str | None = None,
    ) -> None:
        if "{prompt}" not in template:
            raise ValueError("template_jailbreak template must contain '{prompt}'")
        self.template = template

    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text=self.template.format(prompt=prompt.text), metadata=prompt.metadata)
