from __future__ import annotations

from airedteam.core.types import Prompt

DEFAULT_MAP = {"a": "@", "e": "3", "i": "1", "o": "0", "s": "$", "t": "7"}


class LeetspeakConverter:
    """Rewrite letters to common leet equivalents."""

    name = "leetspeak"

    def __init__(self, *, mapping: dict[str, str] | None = None, case_sensitive: bool = False) -> None:
        self.mapping = mapping or DEFAULT_MAP
        self.case_sensitive = case_sensitive

    async def convert(self, prompt: Prompt) -> Prompt:
        out: list[str] = []
        for ch in prompt.text:
            key = ch if self.case_sensitive else ch.lower()
            out.append(self.mapping.get(key, ch))
        return Prompt(text="".join(out), metadata=prompt.metadata)
