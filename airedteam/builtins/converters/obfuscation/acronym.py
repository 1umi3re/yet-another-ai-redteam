from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class AcronymConverter:
    """Convert words into an acronym."""

    name = "acronym"

    def __init__(self, *, separator: str = ".", trailing_separator: bool = True) -> None:
        self.separator = separator
        self.trailing_separator = trailing_separator

    async def convert(self, prompt: Prompt) -> Prompt:
        letters = [word[0].upper() for word in prompt.text.split() if word]
        text = self.separator.join(letters)
        if self.trailing_separator and text:
            text = f"{text}{self.separator}"
        return converted_prompt(prompt, text)
