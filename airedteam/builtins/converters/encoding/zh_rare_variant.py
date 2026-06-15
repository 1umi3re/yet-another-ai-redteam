from __future__ import annotations

from airedteam.builtins.converters.support.chinese import RARE_VARIANT_MAP, maybe_replace_chars, wrap_decode_instruction
from airedteam.core.types import Prompt


class ZhRareVariantConverter:
    """Replace common Chinese characters with rare or variant forms."""

    name = "zh_rare_variant"

    def __init__(self, *, probability: str | float = "0.5", seed: str = "", wrap: bool = False) -> None:
        self.probability = probability
        self.seed = seed
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        text = maybe_replace_chars(prompt.text, RARE_VARIANT_MAP, probability=self.probability, seed=self.seed)
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="异体字")
