from __future__ import annotations

from airedteam.builtins.converters.support.chinese import join_tokens, pinyin_tokens, wrap_decode_instruction
from airedteam.core.types import Prompt


class ZhPinyinConverter:
    """Convert Chinese characters to Hanyu Pinyin."""

    name = "zh_pinyin"

    def __init__(self, *, tone: str = "number", separator: str = " ", wrap: bool = False) -> None:
        self.tone = tone
        self.separator = separator
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        text = join_tokens(pinyin_tokens(prompt.text, tone=self.tone), self.separator)
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="拼音")
