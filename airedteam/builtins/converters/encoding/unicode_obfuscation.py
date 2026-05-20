from __future__ import annotations
from typing import Literal
from airedteam.core.types import Prompt


_HOMOGLYPHS = {
    "a": "а", "c": "с", "e": "е", "i": "і", "o": "о", "p": "р", "s": "ѕ", "x": "х",
}


class UnicodeObfuscationConverter:
    """Insert zero-width characters or replace latin letters with Cyrillic homoglyphs."""
    name = "unicode_obfuscation"

    def __init__(
        self, *, strategy: Literal["zero_width", "homoglyph"] = "zero_width",
        every: int = 2,
    ) -> None:
        self.strategy = strategy
        self.every = max(1, every)

    async def convert(self, prompt: Prompt) -> Prompt:
        if self.strategy == "zero_width":
            out_chars = []
            for i, ch in enumerate(prompt.text):
                out_chars.append(ch)
                if (i + 1) % self.every == 0 and i != len(prompt.text) - 1:
                    out_chars.append("\u200b")
            return Prompt(text="".join(out_chars), metadata=prompt.metadata)
        if self.strategy == "homoglyph":
            return Prompt(
                text="".join(_HOMOGLYPHS.get(ch, ch) for ch in prompt.text),
                metadata=prompt.metadata,
            )
        raise ValueError(f"unknown strategy {self.strategy!r}")
