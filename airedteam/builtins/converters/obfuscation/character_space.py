from __future__ import annotations

from airedteam.core.types import Prompt


class CharacterSpaceConverter:
    """Insert spaces between every character in the prompt."""

    name = "character_space"

    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text=" ".join(prompt.text), metadata=prompt.metadata)
