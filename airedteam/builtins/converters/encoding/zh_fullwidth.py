from __future__ import annotations

from airedteam.builtins.converters.support.chinese import fullwidth_text, wrap_decode_instruction
from airedteam.core.types import Prompt


class ZhFullwidthConverter:
    """Convert ASCII letters, digits, and punctuation to fullwidth forms."""

    name = "zh_fullwidth"

    def __init__(self, *, wrap: bool = False) -> None:
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        return wrap_decode_instruction(prompt, fullwidth_text(prompt.text), enabled=self.wrap, label="全角")
