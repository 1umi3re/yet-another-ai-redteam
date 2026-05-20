from __future__ import annotations

from airedteam.core.types import Prompt


class UnicodeEscapeConverter:
    """Render every character as a Unicode escape sequence."""

    name = "unicode_escape"

    def __init__(self, *, uppercase_hex: bool = True, separator: str = "") -> None:
        self.uppercase_hex = uppercase_hex
        self.separator = separator

    async def convert(self, prompt: Prompt) -> Prompt:
        escaped = []
        for ch in prompt.text:
            if self.uppercase_hex:
                escaped.append(f"\\u{ord(ch):04X}")
            else:
                escaped.append(f"\\u{ord(ch):04x}")
        return Prompt(text=self.separator.join(escaped), metadata=prompt.metadata)
