from __future__ import annotations

from airedteam.builtins.converters.support.chinese import (
    MARS_TEXT_MAP,
    fullwidth_text,
    maybe_replace_chars,
    wrap_decode_instruction,
)
from airedteam.core.types import Prompt


class ZhMarsTextConverter:
    """Convert Chinese text into a Mars-text style mix of variants and symbols."""

    name = "zh_mars_text"

    def __init__(self, *, probability: str | float = "0.75", seed: str = "", wrap: bool = False) -> None:
        self.probability = probability
        self.seed = seed
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        text = maybe_replace_chars(prompt.text, MARS_TEXT_MAP, probability=self.probability, seed=self.seed)
        text = fullwidth_text(text)
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="火星文")
