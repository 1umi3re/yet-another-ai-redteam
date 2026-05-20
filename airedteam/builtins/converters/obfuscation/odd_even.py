from __future__ import annotations

from airedteam.core.types import Prompt


class OddEvenConverter:
    """Move odd-positioned words before even-positioned words."""

    name = "odd_even"

    async def convert(self, prompt: Prompt) -> Prompt:
        words = prompt.text.split()
        text = " ".join(words[::2] + words[1::2])
        return Prompt(text=text, metadata=prompt.metadata)
