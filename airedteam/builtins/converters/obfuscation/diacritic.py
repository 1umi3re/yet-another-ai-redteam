from __future__ import annotations

from airedteam.core.types import Prompt

_MARKS = {
    "acute": "\u0301",
    "grave": "\u0300",
    "tilde": "\u0303",
    "dot": "\u0307",
    "macron": "\u0304",
}


class DiacriticConverter:
    """Add a selected combining diacritic mark after visible characters."""

    name = "diacritic"

    def __init__(self, *, mark: str = "acute") -> None:
        self.mark = _MARKS.get(mark, mark)

    async def convert(self, prompt: Prompt) -> Prompt:
        text = "".join(ch if ch.isspace() else f"{ch}{self.mark}" for ch in prompt.text)
        return Prompt(text=text, metadata=prompt.metadata)
