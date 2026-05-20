from __future__ import annotations

from airedteam.core.types import Prompt


class BinAsciiConverter:
    """Encode text as 8-bit ASCII/UTF-8 binary groups."""

    name = "bin_ascii"

    def __init__(self, *, separator: str = " ") -> None:
        self.separator = separator

    async def convert(self, prompt: Prompt) -> Prompt:
        encoded = self.separator.join(f"{byte:08b}" for byte in prompt.text.encode("utf-8"))
        return Prompt(text=encoded, metadata=prompt.metadata)
