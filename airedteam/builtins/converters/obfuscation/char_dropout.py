from __future__ import annotations

import random

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class CharDropoutConverter:
    """Randomly delete characters with a configurable probability."""

    name = "char_dropout"

    def __init__(self, *, probability: float = 0.1, seed: int | None = None) -> None:
        self.probability = max(0.0, min(1.0, float(probability)))
        self.seed = None if seed in ("", None) else int(seed)

    async def convert(self, prompt: Prompt) -> Prompt:
        rng = random.Random(self.seed)
        text = "".join(ch for ch in prompt.text if rng.random() >= self.probability)
        return converted_prompt(prompt, text)
