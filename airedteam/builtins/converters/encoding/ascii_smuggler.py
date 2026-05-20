from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class AsciiSmugglerConverter:
    """Hide ASCII characters as Unicode tag characters after visible carrier text."""

    name = "ascii_smuggler"

    def __init__(self, *, carrier_text: str = "") -> None:
        self.carrier_text = carrier_text

    async def convert(self, prompt: Prompt) -> Prompt:
        encoded = "".join(self._tag(ch) for ch in prompt.text)
        return converted_prompt(prompt, f"{self.carrier_text}{encoded}")

    def _tag(self, char: str) -> str:
        code_point = ord(char)
        if 0x00 <= code_point <= 0x7F:
            return chr(0xE0000 + code_point)
        return char
