from __future__ import annotations

from typing import Literal

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class ControlCharsRepetitionConverter:
    """Append or prepend repeated control characters to the prompt."""

    name = "control_chars_repetition"

    def __init__(
        self,
        *,
        char: str = "\r",
        repetitions: int = 1000,
        position: Literal["prefix", "suffix", "both"] = "suffix",
    ) -> None:
        self.char = char or "\r"
        self.repetitions = max(0, int(repetitions))
        self.position = position

    async def convert(self, prompt: Prompt) -> Prompt:
        padding = self.char * self.repetitions
        if self.position == "prefix":
            text = f"{padding}{prompt.text}"
        elif self.position == "both":
            text = f"{padding}{prompt.text}{padding}"
        else:
            text = f"{prompt.text}{padding}"
        return converted_prompt(prompt, text)
