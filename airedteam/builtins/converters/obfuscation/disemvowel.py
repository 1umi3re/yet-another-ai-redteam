from __future__ import annotations

from airedteam.core.types import Prompt


_VOWELS = frozenset("aeiouAEIOU")


class DisemvowelConverter:
    """Remove vowels from the prompt text."""

    name = "disemvowel"

    async def convert(self, prompt: Prompt) -> Prompt:
        text = "".join(ch for ch in prompt.text if ch not in _VOWELS)
        return Prompt(text=text, metadata=prompt.metadata)
