from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt

_HOMOGLYPHS = str.maketrans(
    {
        "A": "Α",
        "B": "Β",
        "C": "С",
        "E": "Ε",
        "H": "Η",
        "I": "Ι",
        "K": "Κ",
        "M": "Μ",
        "O": "Ο",
        "P": "Ρ",
        "S": "Ѕ",
        "T": "Τ",
        "X": "Χ",
        "Y": "Υ",
        "a": "а",
        "c": "с",
        "e": "е",
        "i": "і",
        "o": "о",
        "p": "р",
        "s": "ѕ",
        "x": "х",
        "y": "у",
    }
)


class HomoglyphConverter:
    """Promptfoo-style Unicode confusable-character substitution."""

    name = "homoglyph"

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, prompt.text.translate(_HOMOGLYPHS))
