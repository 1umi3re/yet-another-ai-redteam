from __future__ import annotations

from airedteam.core.types import Prompt


_MARKS = [
    "\u0300",
    "\u0301",
    "\u0302",
    "\u0303",
    "\u0304",
    "\u0305",
    "\u0306",
    "\u0307",
]


class ZalgoConverter:
    """Add deterministic combining marks to visible characters."""

    name = "zalgo"

    def __init__(self, *, marks_per_char: int = 2) -> None:
        self.marks_per_char = max(0, int(marks_per_char))

    async def convert(self, prompt: Prompt) -> Prompt:
        marks = "".join(_MARKS[: self.marks_per_char])
        out = []
        for ch in prompt.text:
            out.append(ch if ch.isspace() else f"{ch}{marks}")
        return Prompt(text="".join(out), metadata=prompt.metadata)
