from __future__ import annotations

from typing import Any

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class PromptFramingTemplateConverter:
    """Converter backed by a target-facing attack prompt template."""

    def __init__(
        self,
        *,
        method_name: str,
        template: str,
        variables: dict[str, Any] | None = None,
    ) -> None:
        if "{prompt}" not in template:
            raise ValueError("attack method template must contain '{prompt}'")
        self.name = method_name
        self.template = template
        self.variables = dict(variables or {})

    async def convert(self, prompt: Prompt) -> Prompt:
        values = {key: str(value) for key, value in self.variables.items()}
        values["prompt"] = prompt.text
        return converted_prompt(prompt, self.template.format(**values))
