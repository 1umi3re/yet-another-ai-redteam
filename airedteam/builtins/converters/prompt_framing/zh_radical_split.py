from __future__ import annotations

from airedteam.builtins.converters.support.chinese import RADICAL_SPLIT_MAP, is_cjk, wrap_decode_instruction
from airedteam.core.types import Prompt


class ZhRadicalSplitConverter:
    """Split selected Chinese characters into radical-like components."""

    name = "zh_radical_split"

    def __init__(self, *, separator: str = " ", wrap: bool = True) -> None:
        self.separator = separator
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        parts = [f"{char}={RADICAL_SPLIT_MAP.get(char, char)}" for char in prompt.text if is_cjk(char)]
        text = self.separator.join(parts) if parts else prompt.text
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="偏旁拆字")
