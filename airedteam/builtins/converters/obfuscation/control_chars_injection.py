from __future__ import annotations

from typing import Literal

from airedteam.core.types import Prompt


class ControlCharsInjectionConverter:
    """Inject ASCII control characters around or inside prompt text."""

    name = "control_chars_injection"

    def __init__(
        self,
        *,
        mode: Literal["delimit", "prefix", "intersperse"] = "delimit",
        char: str = "\x1e",
    ) -> None:
        self.mode = mode
        self.char = char

    async def convert(self, prompt: Prompt) -> Prompt:
        if self.mode == "prefix":
            text = f"{self.char}{prompt.text}"
        elif self.mode == "intersperse":
            text = self.char.join(prompt.text)
        else:
            text = f"\x1e{prompt.text}\x1f"
        return Prompt(text=text, metadata=prompt.metadata)
