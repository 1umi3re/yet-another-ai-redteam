from __future__ import annotations

import re

from airedteam.core.types import Prompt

DEFAULT_REPLACEMENTS = {
    "bomb": "device",
    "gun": "tool",
    "weapon": "object",
    "malware": "software",
    "password": "credential",
}


class DenylistConverter:
    """Replace configured sensitive words or phrases with substitutes."""

    name = "denylist"

    def __init__(
        self,
        *,
        replacements: dict[str, str] | None = None,
        case_sensitive: bool = False,
    ) -> None:
        self.replacements = replacements or DEFAULT_REPLACEMENTS
        self.case_sensitive = case_sensitive

    async def convert(self, prompt: Prompt) -> Prompt:
        text = prompt.text
        flags = 0 if self.case_sensitive else re.IGNORECASE
        for source, replacement in self.replacements.items():
            text = re.sub(re.escape(source), replacement, text, flags=flags)
        return Prompt(text=text, metadata=prompt.metadata)
