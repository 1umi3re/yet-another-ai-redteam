from __future__ import annotations

import re

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


DEFAULT_REPLACEMENTS = {
    "ignore": "disregard",
    "instruction": "direction",
    "instructions": "directions",
    "reveal": "disclose",
    "secret": "private detail",
    "secrets": "private details",
    "rules": "guidelines",
}


class WordSubstitutionConverter:
    """Replace selected words with configurable synonyms."""

    name = "word_substitution"

    def __init__(self, *, replacements: dict[str, str] | None = None) -> None:
        self.replacements = replacements or DEFAULT_REPLACEMENTS

    async def convert(self, prompt: Prompt) -> Prompt:
        pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in self.replacements) + r")\b", re.IGNORECASE)
        return converted_prompt(prompt, pattern.sub(self._replace, prompt.text))

    def _replace(self, match: re.Match[str]) -> str:
        source = match.group(0)
        replacement = self.replacements[source.lower()]
        if source[:1].isupper():
            return replacement[:1].upper() + replacement[1:]
        return replacement
