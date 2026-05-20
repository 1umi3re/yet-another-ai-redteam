from __future__ import annotations

import random
from collections.abc import Sequence

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class WordMixinConverter:
    """Insert configured words at a periodic word interval."""

    name = "word_mixin"

    def __init__(
        self,
        *,
        words: Sequence[str] | str = ("red", "blue", "green"),
        every: int = 3,
        seed: int | None = None,
    ) -> None:
        if isinstance(words, str):
            parsed = [word.strip() for word in words.split(",") if word.strip()]
        else:
            parsed = [str(word) for word in words if str(word)]
        self.words = parsed or ["red", "blue", "green"]
        self.every = max(1, int(every))
        self.seed = None if seed in ("", None) else int(seed)

    async def convert(self, prompt: Prompt) -> Prompt:
        rng = random.Random(self.seed)
        output: list[str] = []
        for index, word in enumerate(prompt.text.split(), start=1):
            output.append(word)
            if index % self.every == 0:
                output.append(rng.choice(self.words))
        return converted_prompt(prompt, " ".join(output))
