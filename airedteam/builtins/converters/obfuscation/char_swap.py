from __future__ import annotations

import re

from airedteam.core.types import Prompt


class CharSwapConverter:
    """Swap adjacent inner characters in words while preserving word boundaries."""

    name = "char_swap"

    def __init__(self, *, max_iterations: int = 1, min_word_length: int = 4) -> None:
        self.max_iterations = max(1, int(max_iterations))
        self.min_word_length = max(4, int(min_word_length))

    async def convert(self, prompt: Prompt) -> Prompt:
        pattern = re.compile(rf"[A-Za-z]{{{self.min_word_length},}}")
        return Prompt(
            text=pattern.sub(lambda match: self._swap_word(match.group(0)), prompt.text),
            metadata=prompt.metadata,
        )

    def _swap_word(self, word: str) -> str:
        chars = list(word)
        idx = 1
        for _ in range(self.max_iterations):
            if idx >= len(chars) - 2:
                break
            chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
            idx += 2
        return "".join(chars)
