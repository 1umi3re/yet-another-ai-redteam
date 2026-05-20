from __future__ import annotations

from airedteam.core.types import Prompt


class LengthConverter:
    """Encode words as word-to-original-index mappings sorted by word length."""

    name = "length"

    async def convert(self, prompt: Prompt) -> Prompt:
        words = prompt.text.split()
        indexed_words = sorted(enumerate(words), key=lambda item: len(item[1]))
        encoded = [{word: index} for index, word in indexed_words]
        return Prompt(text=repr(encoded), metadata=prompt.metadata)
