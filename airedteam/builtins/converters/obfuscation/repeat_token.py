from __future__ import annotations

from typing import Literal

from airedteam.core.types import Prompt


class RepeatTokenConverter:
    """Repeat a token before, after, or around the prompt."""

    name = "repeat_token"

    def __init__(
        self,
        *,
        token: str = "!",
        count: int = 10,
        position: Literal["prefix", "suffix", "both"] = "suffix",
    ) -> None:
        self.token = token
        self.count = max(0, int(count))
        self.position = position

    async def convert(self, prompt: Prompt) -> Prompt:
        repeated = self.token * self.count
        if self.position == "prefix":
            text = f"{repeated}{prompt.text}"
        elif self.position == "both":
            text = f"{repeated}{prompt.text}{repeated}"
        else:
            text = f"{prompt.text}{repeated}"
        return Prompt(text=text, metadata=prompt.metadata)
