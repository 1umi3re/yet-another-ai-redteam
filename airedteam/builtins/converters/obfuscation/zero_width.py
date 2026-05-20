from __future__ import annotations

from airedteam.core.types import Prompt


class ZeroWidthConverter:
    """Insert a zero-width character after every N visible characters."""

    name = "zero_width"

    def __init__(self, *, every: int = 2, char: str = "\u200b") -> None:
        self.every = max(1, int(every))
        self.char = char

    async def convert(self, prompt: Prompt) -> Prompt:
        out: list[str] = []
        for i, ch in enumerate(prompt.text):
            out.append(ch)
            if (i + 1) % self.every == 0 and i != len(prompt.text) - 1:
                out.append(self.char)
        return Prompt(text="".join(out), metadata=prompt.metadata)
