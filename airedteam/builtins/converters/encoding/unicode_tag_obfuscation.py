from __future__ import annotations

from airedteam.core.types import Prompt


class UnicodeTagObfuscationConverter:
    """Encode visible ASCII characters as Unicode tag characters."""

    name = "unicode_tag_obfuscation"

    def __init__(self, *, carrier_text: str = "") -> None:
        self.carrier_text = carrier_text

    async def convert(self, prompt: Prompt) -> Prompt:
        encoded = "".join(self._tag(ch) for ch in prompt.text)
        return Prompt(text=f"{self.carrier_text}{encoded}", metadata=prompt.metadata)

    def _tag(self, ch: str) -> str:
        code = ord(ch)
        if 0x20 <= code <= 0x7E:
            return chr(0xE0000 + code)
        return ch
