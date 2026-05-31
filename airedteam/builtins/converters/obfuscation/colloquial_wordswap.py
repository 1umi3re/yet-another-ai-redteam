from __future__ import annotations

import re

from airedteam.core.types import Prompt

DEFAULT_SWAPS = {
    "you": "u",
    "your": "ur",
    "are": "r",
    "please": "plz",
    "people": "ppl",
    "because": "bc",
    "before": "b4",
    "for": "4",
    "to": "2",
    "too": "2",
}


class ColloquialWordswapConverter:
    """Replace common words with colloquial short forms."""

    name = "colloquial_wordswap"

    def __init__(self, *, swaps: dict[str, str] | None = None) -> None:
        self.swaps = swaps or DEFAULT_SWAPS

    async def convert(self, prompt: Prompt) -> Prompt:
        pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in self.swaps) + r")\b", re.I)
        text = pattern.sub(lambda match: self.swaps[match.group(0).lower()], prompt.text)
        return Prompt(text=text, metadata=prompt.metadata)
