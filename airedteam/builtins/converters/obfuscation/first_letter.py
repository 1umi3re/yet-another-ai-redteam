from __future__ import annotations

import re

from airedteam.core.types import Prompt


class FirstLetterConverter:
    """Collapse words to their first letters."""

    name = "first_letter"

    def __init__(self, *, separator: str = "") -> None:
        self.separator = separator

    async def convert(self, prompt: Prompt) -> Prompt:
        words = re.findall(r"[A-Za-z0-9]+", prompt.text)
        return Prompt(text=self.separator.join(word[0] for word in words), metadata=prompt.metadata)
