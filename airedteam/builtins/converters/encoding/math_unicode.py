from __future__ import annotations

from airedteam.core.types import Prompt


class MathUnicodeConverter:
    """Replace ASCII letters and digits with mathematical bold Unicode characters."""

    name = "math_unicode"

    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text="".join(self._convert_char(ch) for ch in prompt.text), metadata=prompt.metadata)

    def _convert_char(self, ch: str) -> str:
        if "A" <= ch <= "Z":
            return chr(0x1D400 + ord(ch) - ord("A"))
        if "a" <= ch <= "z":
            return chr(0x1D41A + ord(ch) - ord("a"))
        if "0" <= ch <= "9":
            return chr(0x1D7CE + ord(ch) - ord("0"))
        return ch
