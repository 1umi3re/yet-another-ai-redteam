from __future__ import annotations
from airedteam.core.types import Prompt


SUBS = {
    "bomb": "💣", "gun": "🔫", "knife": "🔪", "fire": "🔥",
    "money": "💰", "key": "🔑", "poison": "☠",
}


class EmojiSubstitutionConverter:
    """Replace flagged keywords with their emoji equivalents."""
    name = "emoji_substitution"

    def __init__(self, *, words: dict[str, str] | None = None) -> None:
        self.words = words or SUBS

    async def convert(self, prompt):
        txt = prompt.text
        for w, e in self.words.items():
            txt = txt.replace(w, e)
        return Prompt(text=txt, metadata=prompt.metadata)
