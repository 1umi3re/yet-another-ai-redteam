from __future__ import annotations

import random

from airedteam.core.types import Prompt


class RandomCaseConverter:
    """Randomly uppercase alphabetic characters using an optional deterministic seed."""

    name = "random_case"

    def __init__(self, *, uppercase_probability: float = 0.5, seed: int | None = None) -> None:
        self.uppercase_probability = max(0.0, min(1.0, float(uppercase_probability)))
        self.seed = None if seed in ("", None) else int(seed)

    async def convert(self, prompt: Prompt) -> Prompt:
        rng = random.Random(self.seed)
        out: list[str] = []
        for ch in prompt.text:
            if ch.isalpha():
                out.append(ch.upper() if rng.random() < self.uppercase_probability else ch.lower())
            else:
                out.append(ch)
        return Prompt(text="".join(out), metadata=prompt.metadata)
