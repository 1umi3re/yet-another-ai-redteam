from __future__ import annotations

from airedteam.builtins.converters.support.chinese import (
    HOMOPHONE_MAP,
    is_cjk,
    join_tokens,
    parse_probability,
    pinyin_tokens,
    rng_from_seed,
    wrap_decode_instruction,
    zhuyin_tokens,
)
from airedteam.core.types import Prompt


class ZhMixedNotationConverter:
    """Mix Chinese characters with Pinyin, Zhuyin, or homophone notation."""

    name = "zh_mixed_notation"

    def __init__(
        self,
        *,
        mode: str = "mixed",
        probability: str | float = "0.5",
        separator: str = " ",
        seed: str = "",
        wrap: bool = False,
    ) -> None:
        self.mode = mode
        self.probability = probability
        self.separator = separator
        self.seed = seed
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        rng = rng_from_seed(self.seed)
        threshold = parse_probability(self.probability)
        tokens: list[str] = []
        for char in prompt.text:
            if not is_cjk(char) or rng.random() > threshold:
                tokens.append(char)
                continue
            mode = self.mode
            if mode == "mixed":
                mode = rng.choice(["pinyin", "zhuyin", "homophone"])
            if mode == "zhuyin":
                tokens.append(zhuyin_tokens(char)[0])
            elif mode == "homophone":
                key = pinyin_tokens(char, tone="none")[0]
                choices = HOMOPHONE_MAP.get(key)
                tokens.append(rng.choice(choices) if choices else pinyin_tokens(char, tone="none")[0])
            else:
                tokens.append(pinyin_tokens(char, tone="none")[0])
        text = join_tokens(tokens, self.separator)
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="中文混写")
