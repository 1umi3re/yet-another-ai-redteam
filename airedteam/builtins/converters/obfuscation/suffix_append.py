from __future__ import annotations

from airedteam.core.types import Prompt


class SuffixAppendConverter:
    """Append a fixed suffix to the prompt."""

    name = "suffix_append"

    def __init__(self, *, suffix: str = "") -> None:
        if not suffix:
            raise ValueError("suffix_append requires a non-empty 'suffix' param")
        self.suffix = suffix

    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text=f"{prompt.text}{self.suffix}", metadata=prompt.metadata)
