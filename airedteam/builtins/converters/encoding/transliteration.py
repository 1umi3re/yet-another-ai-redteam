from __future__ import annotations

from airedteam.core.types import Prompt
from airedteam.builtins.converters.support.template_helpers import converted_prompt


_MAP = str.maketrans({
    "a": "а",
    "A": "А",
    "c": "с",
    "C": "С",
    "e": "е",
    "E": "Е",
    "o": "о",
    "O": "О",
    "p": "р",
    "P": "Р",
    "x": "х",
    "X": "Х",
    "y": "у",
    "Y": "У",
})


class TransliterationConverter:
    """Transliterate common Latin letters into cross-script homoglyphs."""

    name = "transliteration"

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, prompt.text.translate(_MAP))
