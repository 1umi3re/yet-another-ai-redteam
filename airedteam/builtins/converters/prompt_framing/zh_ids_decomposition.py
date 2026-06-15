from __future__ import annotations

from airedteam.builtins.converters.support.chinese import IDS_MAP, is_cjk, wrap_decode_instruction
from airedteam.core.types import Prompt


class ZhIdsDecompositionConverter:
    """Represent selected Chinese characters with IDS decomposition notation."""

    name = "zh_ids_decomposition"

    def __init__(self, *, separator: str = " ", wrap: bool = True) -> None:
        self.separator = separator
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        parts = [f"{char}={IDS_MAP.get(char, char)}" for char in prompt.text if is_cjk(char)]
        text = self.separator.join(parts) if parts else prompt.text
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="IDS 表意描述")
