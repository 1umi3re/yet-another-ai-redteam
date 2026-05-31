from __future__ import annotations

from airedteam.core.types import Prompt


class NoiseConverter:
    """Insert a fixed noise character after every N characters."""

    name = "noise"

    def __init__(self, *, char: str = "~", every: int = 3) -> None:
        self.char = char
        self.every = max(1, int(every))

    async def convert(self, prompt: Prompt) -> Prompt:
        chunks = [prompt.text[i : i + self.every] for i in range(0, len(prompt.text), self.every)]
        return Prompt(text=self.char.join(chunks), metadata=prompt.metadata)
