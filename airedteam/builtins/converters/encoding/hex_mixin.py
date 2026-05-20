from __future__ import annotations

import random

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class HexMixinConverter:
    """Insert random hexadecimal marker tokens at a periodic word interval."""

    name = "hex_mixin"

    def __init__(
        self,
        *,
        every: int = 3,
        digits: int = 6,
        seed: int | None = None,
    ) -> None:
        self.every = max(1, int(every))
        self.digits = max(1, int(digits))
        self.seed = None if seed in ("", None) else int(seed)

    async def convert(self, prompt: Prompt) -> Prompt:
        rng = random.Random(self.seed)
        output: list[str] = []
        for index, word in enumerate(prompt.text.split(), start=1):
            output.append(word)
            if index % self.every == 0:
                token = "".join(rng.choice("0123456789ABCDEF") for _ in range(self.digits))
                output.append(f"{{<{token}>}}")
        return converted_prompt(prompt, " ".join(output))
