from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class ASCIISmugglingConverter:
    """Insert invisible ASCII control characters between prompt characters."""

    name = "ascii_smuggling"

    def __init__(self, *, char: str = "\b") -> None:
        self.char = char or "\b"

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, self.char.join(prompt.text))
