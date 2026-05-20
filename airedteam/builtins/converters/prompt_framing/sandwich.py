from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class SandwichConverter:
    """Place the payload between benign-looking framing text."""

    name = "sandwich"

    def __init__(
        self,
        *,
        benign_prefix: str = "Summarize the following policy note before answering.",
        benign_suffix: str = "Then provide a concise compliance rationale.",
    ) -> None:
        self.benign_prefix = benign_prefix
        self.benign_suffix = benign_suffix

    async def convert(self, prompt: Prompt) -> Prompt:
        text = f"{self.benign_prefix}\n\n{prompt.text}\n\n{self.benign_suffix}"
        return converted_prompt(prompt, text)
