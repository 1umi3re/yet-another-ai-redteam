from __future__ import annotations

from typing import Literal

from airedteam.core.types import Prompt


class SelectiveTextConverter:
    """Apply a wrapper to one selected portion of the prompt text."""

    name = "selective_text"

    def __init__(
        self,
        *,
        mode: Literal["first_half", "second_half", "first_word", "last_word"] = "first_half",
        wrapper: str = "[{text}]",
    ) -> None:
        if "{text}" not in wrapper:
            raise ValueError("selective_text wrapper must contain '{text}'")
        self.mode = mode
        self.wrapper = wrapper

    async def convert(self, prompt: Prompt) -> Prompt:
        text = prompt.text
        if self.mode == "second_half":
            split = len(text) // 2
            out = f"{text[:split]}{self.wrapper.format(text=text[split:])}"
        elif self.mode == "first_word":
            parts = text.split(" ", 1)
            out = self._wrap_word(parts)
        elif self.mode == "last_word":
            parts = text.rsplit(" ", 1)
            if len(parts) == 1:
                out = self.wrapper.format(text=text)
            else:
                out = f"{parts[0]} {self.wrapper.format(text=parts[1])}"
        else:
            split = len(text) // 2
            out = f"{self.wrapper.format(text=text[:split])}{text[split:]}"
        return Prompt(text=out, metadata=prompt.metadata)

    def _wrap_word(self, parts: list[str]) -> str:
        if len(parts) == 1:
            return self.wrapper.format(text=parts[0])
        return f"{self.wrapper.format(text=parts[0])} {parts[1]}"
