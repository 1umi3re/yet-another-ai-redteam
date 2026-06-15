from __future__ import annotations

from airedteam.builtins.converters.support.chinese import (
    UNICODE_COMPAT_MAP,
    maybe_replace_chars,
    wrap_decode_instruction,
)
from airedteam.core.types import Prompt


class ZhUnicodeCompatConverter:
    """Replace Chinese characters with CJK compatibility or near-compatibility forms."""

    name = "zh_unicode_compat"

    def __init__(self, *, probability: str | float = "0.5", seed: str = "", wrap: bool = False) -> None:
        self.probability = probability
        self.seed = seed
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        text = maybe_replace_chars(prompt.text, UNICODE_COMPAT_MAP, probability=self.probability, seed=self.seed)
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="CJK 兼容字形")
