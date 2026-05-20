from __future__ import annotations

import random
import re

from airedteam.core.types import Prompt


class WordScrambleConverter:
    """Shuffle inner letters of words, preserving first and last character."""

    name = "word_scramble"

    def __init__(self, *, seed: int | None = None, min_word_length: int = 4) -> None:
        self.seed = None if seed in ("", None) else int(seed)
        self.min_word_length = max(4, int(min_word_length))

    async def convert(self, prompt: Prompt) -> Prompt:
        rng = random.Random(self.seed)
        pattern = re.compile(rf"[A-Za-z]{{{self.min_word_length},}}")
        return Prompt(
            text=pattern.sub(lambda match: self._scramble_word(match.group(0), rng), prompt.text),
            metadata=prompt.metadata,
        )

    def _scramble_word(self, word: str, rng: random.Random) -> str:
        if len(word) <= 3:
            return word
        inner = list(word[1:-1])
        original = list(inner)
        rng.shuffle(inner)
        if inner == original and len(inner) > 1:
            inner = inner[1:] + inner[:1]
        return f"{word[0]}{''.join(inner)}{word[-1]}"
