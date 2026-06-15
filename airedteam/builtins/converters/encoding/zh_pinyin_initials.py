from __future__ import annotations

from airedteam.builtins.converters.support.chinese import join_tokens, pinyin_initial_tokens, wrap_decode_instruction
from airedteam.core.types import Prompt


class ZhPinyinInitialsConverter:
    """Compress Chinese text into Pinyin initials."""

    name = "zh_pinyin_initials"

    def __init__(self, *, separator: str = "", wrap: bool = False) -> None:
        self.separator = separator
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        text = join_tokens(pinyin_initial_tokens(prompt.text), self.separator)
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="拼音首字母")
