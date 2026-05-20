from __future__ import annotations

import re

from airedteam.core.types import Prompt


class CamelCaseConverter:
    """Transform prompt text into camelCase tokens."""

    name = "camel_case"

    async def convert(self, prompt: Prompt) -> Prompt:
        words = re.findall(r"[A-Za-z0-9]+", prompt.text)
        if not words:
            return Prompt(text="", metadata=prompt.metadata)
        first, rest = words[0].lower(), words[1:]
        text = first + "".join(word[:1].upper() + word[1:].lower() for word in rest)
        return Prompt(text=text, metadata=prompt.metadata)
