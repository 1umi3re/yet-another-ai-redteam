from __future__ import annotations

import re

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class TokenBreakConverter:
    """Prefix trigger words to break simple token-based filters."""

    name = "token_break"

    def __init__(self, *, breaker: str = "~", triggers: list[str] | None = None) -> None:
        self.breaker = breaker
        self.triggers = triggers or ["ignore", "system", "instructions", "secret", "password"]

    async def convert(self, prompt: Prompt) -> Prompt:
        text = prompt.text
        for trigger in self.triggers:
            text = re.sub(
                rf"\b{re.escape(trigger)}\b",
                f"{self.breaker}{trigger}",
                text,
                flags=re.IGNORECASE,
            )
        return converted_prompt(prompt, text)
