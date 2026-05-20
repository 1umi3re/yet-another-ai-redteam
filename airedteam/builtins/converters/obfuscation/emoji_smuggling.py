from __future__ import annotations

from airedteam.core.types import Prompt


class EmojiSmugglingConverter:
    """Hide UTF-8 bytes inside emoji variation selectors."""

    name = "emoji_smuggling"

    def __init__(self, *, carrier: str = "\U0001f600") -> None:
        self.carrier = carrier or "\U0001f600"

    async def convert(self, prompt: Prompt) -> Prompt:
        selectors = []
        for byte in prompt.text.encode("utf-8"):
            selectors.append(chr(0xE0100 + byte))
        return Prompt(text=f"{self.carrier}{''.join(selectors)}", metadata=prompt.metadata)
