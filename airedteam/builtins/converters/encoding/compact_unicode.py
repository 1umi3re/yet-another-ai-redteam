from __future__ import annotations

from airedteam.core.types import Prompt


class CompactUnicodeConverter:
    """Pack UTF-8 bytes into high Unicode code points for compact obfuscation."""

    name = "compact_unicode"

    def __init__(self, *, offset: int = 0x1000) -> None:
        self.offset = int(offset)

    async def convert(self, prompt: Prompt) -> Prompt:
        encoded = "".join(chr(self.offset + byte) for byte in prompt.text.encode("utf-8"))
        return Prompt(text=encoded, metadata=prompt.metadata)
