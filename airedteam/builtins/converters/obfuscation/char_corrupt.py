from __future__ import annotations

import random

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class CharCorruptConverter:
    """Randomly replace characters with a configured token."""

    name = "char_corrupt"

    def __init__(
        self,
        *,
        probability: float = 0.1,
        replacement: str = "*-",
        seed: int | None = None,
    ) -> None:
        self.probability = max(0.0, min(1.0, float(probability)))
        self.replacement = replacement if replacement is not None else "*-"
        self.seed = None if seed in ("", None) else int(seed)

    async def convert(self, prompt: Prompt) -> Prompt:
        rng = random.Random(self.seed)
        text = "".join(self.replacement if rng.random() < self.probability else ch for ch in prompt.text)
        return converted_prompt(prompt, text)
