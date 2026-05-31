from __future__ import annotations

from airedteam.core.types import Prompt


class InsertPunctuationConverter:
    """Insert punctuation after every N characters."""

    name = "insert_punctuation"

    def __init__(self, *, punctuation: str = ".", every: int = 3) -> None:
        self.punctuation = punctuation
        self.every = max(1, int(every))

    async def convert(self, prompt: Prompt) -> Prompt:
        chunks = [prompt.text[i : i + self.every] for i in range(0, len(prompt.text), self.every)]
        return Prompt(text=self.punctuation.join(chunks), metadata=prompt.metadata)
