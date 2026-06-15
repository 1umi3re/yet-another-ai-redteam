from __future__ import annotations

from airedteam.builtins.converters.support.chinese import join_tokens, wrap_decode_instruction, zhuyin_tokens
from airedteam.core.types import Prompt


class ZhZhuyinConverter:
    """Convert Chinese characters to Zhuyin symbols."""

    name = "zh_zhuyin"

    def __init__(self, *, separator: str = " ", wrap: bool = False) -> None:
        self.separator = separator
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        text = join_tokens(zhuyin_tokens(prompt.text), self.separator)
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="注音")
