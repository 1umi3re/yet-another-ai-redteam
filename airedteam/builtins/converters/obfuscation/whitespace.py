from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class WhitespaceConverter:
    """Replace word separators with configurable whitespace."""

    name = "whitespace"

    def __init__(self, *, separator: str = "\n\t") -> None:
        self.separator = separator

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, self.separator.join(prompt.text.split(" ")))
