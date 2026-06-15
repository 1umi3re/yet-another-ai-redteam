from __future__ import annotations

from airedteam.builtins.converters.support.chinese import opencc_convert, wrap_decode_instruction
from airedteam.core.types import Prompt


class ZhSimplifiedTraditionalConverter:
    """Convert Chinese text between simplified and traditional variants."""

    name = "zh_simplified_traditional"

    def __init__(self, *, direction: str = "s2t", wrap: bool = False) -> None:
        self.direction = direction
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        text = opencc_convert(prompt.text, self.direction)
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="简繁转换")
