from __future__ import annotations

from airedteam.core.types import Prompt


class FlipTextConverter:
    """Reverse prompt text."""

    name = "flip_text"

    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text=prompt.text[::-1], metadata=prompt.metadata)
