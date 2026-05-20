from __future__ import annotations

import json

from airedteam.core.types import Prompt


class JsonStringConverter:
    """Render the prompt as a JSON string literal."""

    name = "json_string"

    def __init__(self, *, ensure_ascii: bool = False) -> None:
        self.ensure_ascii = ensure_ascii

    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(
            text=json.dumps(prompt.text, ensure_ascii=self.ensure_ascii),
            metadata=prompt.metadata,
        )
