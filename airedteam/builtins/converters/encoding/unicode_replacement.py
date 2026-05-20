from __future__ import annotations

from airedteam.core.types import Prompt


class UnicodeReplacementConverter:
    """Replace ASCII letters and digits with fullwidth Unicode variants."""

    name = "unicode_replacement"

    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text="".join(self._convert_char(ch) for ch in prompt.text), metadata=prompt.metadata)

    def _convert_char(self, ch: str) -> str:
        code = ord(ch)
        if 0x21 <= code <= 0x7E:
            return chr(code + 0xFEE0)
        if ch == " ":
            return "\u3000"
        return ch
