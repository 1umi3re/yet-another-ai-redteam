from __future__ import annotations

from airedteam.core.types import Prompt

DEFAULT_MAPPING = {
    "a": "\u0251",
    "e": "\u0258",
    "i": "\u026a",
    "o": "\u03bf",
    "u": "\u1d1c",
    "A": "\u0391",
    "B": "\u0392",
    "E": "\u0395",
    "O": "\u039f",
}


class UnicodeSubstitutionConverter:
    """Substitute selected characters or tokens with configured Unicode alternatives."""

    name = "unicode_substitution"

    def __init__(self, *, mapping: dict[str, str] | None = None) -> None:
        self.mapping = mapping or DEFAULT_MAPPING

    async def convert(self, prompt: Prompt) -> Prompt:
        text = prompt.text
        for source, replacement in self.mapping.items():
            text = text.replace(source, replacement)
        return Prompt(text=text, metadata=prompt.metadata)
