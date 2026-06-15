from __future__ import annotations

from airedteam.builtins.converters.support.chinese import (
    HOMOPHONE_MAP,
    is_cjk,
    parse_probability,
    pinyin_tokens,
    rng_from_seed,
    wrap_decode_instruction,
)
from airedteam.core.types import Prompt


class ZhHomophoneConverter:
    """Replace Chinese characters with deterministic homophone candidates."""

    name = "zh_homophone"

    def __init__(self, *, probability: str | float = "0.5", seed: str = "", wrap: bool = False) -> None:
        self.probability = probability
        self.seed = seed
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        rng = rng_from_seed(self.seed)
        threshold = parse_probability(self.probability)
        out: list[str] = []
        for char in prompt.text:
            key = pinyin_tokens(char, tone="none")[0] if is_cjk(char) else ""
            choices = HOMOPHONE_MAP.get(key)
            if choices and rng.random() <= threshold:
                out.append(rng.choice(choices))
            else:
                out.append(char)
        text = "".join(out)
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="同音字")
