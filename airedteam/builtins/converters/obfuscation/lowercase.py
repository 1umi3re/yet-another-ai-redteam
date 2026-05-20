from __future__ import annotations

from airedteam.core.types import Prompt


class LowercaseConverter:
    """Convert prompt text to lowercase."""

    name = "lowercase"

    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text=prompt.text.lower(), metadata=prompt.metadata)
