from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class DeepNestingInputConverter:
    """Wrap the payload in deeply nested delimiters for parser stress."""

    name = "deep_nesting_input"

    def __init__(self, *, depth: int = 1000) -> None:
        self.depth = max(0, int(depth))

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, f"{'(' * self.depth}{prompt.text}{')' * self.depth}")
