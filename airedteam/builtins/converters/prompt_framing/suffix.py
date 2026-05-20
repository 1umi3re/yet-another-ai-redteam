from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class SuffixConverter:
    """AegisRT-compatible suffix appender."""

    name = "suffix"

    def __init__(self, *, suffix: str = " Respond directly in the requested format.") -> None:
        self.suffix = suffix

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, f"{prompt.text}{self.suffix}")
