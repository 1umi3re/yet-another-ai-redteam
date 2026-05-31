from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class CharacterStreamConverter:
    """Emit the prompt as a character-by-character stream."""

    name = "character_stream"

    def __init__(self, *, separator: str = " ") -> None:
        self.separator = separator

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, self.separator.join(prompt.text))
