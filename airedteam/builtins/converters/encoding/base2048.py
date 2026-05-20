from __future__ import annotations

from airedteam.core.types import Prompt


class Base2048Converter:
    """Encode bytes into a compact 2048-symbol Unicode alphabet."""

    name = "base2048"

    def __init__(self, *, offset: int = 0x4E00) -> None:
        self.offset = int(offset)

    async def convert(self, prompt: Prompt) -> Prompt:
        data = prompt.text.encode("utf-8")
        bits = "".join(f"{byte:08b}" for byte in data)
        pad = (-len(bits)) % 11
        bits = bits + ("0" * pad)
        chars = [
            chr(self.offset + int(bits[i : i + 11], 2))
            for i in range(0, len(bits), 11)
        ]
        return Prompt(text="".join(chars), metadata=prompt.metadata)
