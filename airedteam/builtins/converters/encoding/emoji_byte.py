from __future__ import annotations

from airedteam.core.types import Prompt


class EmojiByteConverter:
    """Encode UTF-8 bytes as emoji code points."""

    name = "emoji_byte"

    def __init__(self, *, offset: int = 0x1F600) -> None:
        self.offset = int(offset)

    async def convert(self, prompt: Prompt) -> Prompt:
        encoded = "".join(chr(self.offset + byte) for byte in prompt.text.encode("utf-8"))
        return Prompt(text=encoded, metadata=prompt.metadata)
