from __future__ import annotations

from airedteam.core.types import Prompt


class StringJoinConverter:
    """Insert ``join_value`` between every character in the prompt."""

    name = "string_join"

    def __init__(self, *, join_value: str = " ") -> None:
        self.join_value = join_value

    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text=self.join_value.join(prompt.text), metadata=prompt.metadata)
