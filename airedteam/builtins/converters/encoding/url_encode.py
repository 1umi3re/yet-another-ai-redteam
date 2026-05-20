from __future__ import annotations

from urllib.parse import quote

from airedteam.core.types import Prompt


class UrlEncodeConverter:
    """Percent-encode prompt text."""

    name = "url_encode"

    def __init__(self, *, safe: str = "") -> None:
        self.safe = safe

    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text=quote(prompt.text, safe=self.safe), metadata=prompt.metadata)
