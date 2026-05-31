from __future__ import annotations

from airedteam.core.types import Prompt

_STYLES = {
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "bold": "1",
    "dim": "2",
    "hidden": "8",
}


class AnsiEscapeConverter:
    """Wrap prompt text in ANSI terminal escape sequences."""

    name = "ansi_escape"

    def __init__(self, *, style: str = "hidden") -> None:
        self.style = style

    async def convert(self, prompt: Prompt) -> Prompt:
        code = _STYLES.get(self.style, self.style)
        return Prompt(text=f"\x1b[{code}m{prompt.text}\x1b[0m", metadata=prompt.metadata)
