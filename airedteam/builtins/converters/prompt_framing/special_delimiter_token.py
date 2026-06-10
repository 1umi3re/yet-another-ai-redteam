from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class SpecialDelimiterTokenConverter:
    """Wrap the payload in special chat delimiter tokens."""

    name = "special_delimiter_token"

    def __init__(self, *, start_token: str = "<|im_start|>", end_token: str = "<|im_end|>") -> None:
        self.start_token = start_token
        self.end_token = end_token

    async def convert(self, prompt: Prompt) -> Prompt:
        text = f"{self.start_token}system\n{prompt.text}\n{self.end_token}\n{self.start_token}assistant\n"
        return converted_prompt(prompt, text)
