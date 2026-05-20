from __future__ import annotations

import re

from airedteam.core.types import Prompt
from airedteam.builtins.converters.support.template_helpers import converted_prompt


_WORD = re.compile(r"[A-Za-z]+")
_VOWELS = set("aeiouAEIOU")


def _pig_latin_word(word: str) -> str:
    if not word:
        return word
    if word[0] in _VOWELS:
        return f"{word}way"
    for idx, char in enumerate(word):
        if char in _VOWELS:
            return f"{word[idx:]}{word[:idx]}ay"
    return f"{word}ay"


class PigLatinConverter:
    """Promptfoo-style Pig Latin word transformation."""

    name = "pig_latin"

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, _WORD.sub(lambda m: _pig_latin_word(m.group(0)), prompt.text))
