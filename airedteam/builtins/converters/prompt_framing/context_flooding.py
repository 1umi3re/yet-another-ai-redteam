from __future__ import annotations

from airedteam.core.types import Prompt
from airedteam.builtins.converters.support.template_helpers import converted_prompt


class ContextFloodingConverter:
    """Flood the prompt with benign context before the payload."""

    name = "context_flooding"

    def __init__(self, *, filler: str = "benign context", repetitions: int = 8) -> None:
        self.filler = filler or "benign context"
        self.repetitions = max(0, int(repetitions))

    async def convert(self, prompt: Prompt) -> Prompt:
        prefix = "\n".join(self.filler for _ in range(self.repetitions))
        text = f"{prefix}\n\n{prompt.text}" if prefix else prompt.text
        return converted_prompt(prompt, text)
