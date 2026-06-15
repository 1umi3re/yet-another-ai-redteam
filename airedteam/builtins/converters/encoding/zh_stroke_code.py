from __future__ import annotations

from airedteam.builtins.converters.support.chinese import STROKE_COUNT_MAP, is_cjk, wrap_decode_instruction
from airedteam.core.types import Prompt


class ZhStrokeCodeConverter:
    """Represent selected Chinese characters as stroke-count codes."""

    name = "zh_stroke_code"

    def __init__(self, *, separator: str = " ", wrap: bool = False) -> None:
        self.separator = separator
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        tokens: list[str] = []
        for char in prompt.text:
            if is_cjk(char):
                tokens.append(f"{char}:{STROKE_COUNT_MAP.get(char, '?')}")
            else:
                tokens.append(char)
        text = self.separator.join(tokens)
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="笔画编码")
