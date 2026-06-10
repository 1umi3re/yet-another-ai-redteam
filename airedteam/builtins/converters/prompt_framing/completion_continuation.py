from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class CompletionContinuationConverter:
    """Frame the payload as text that should be continued."""

    name = "completion_continuation"

    def __init__(self, *, lead_in: str = "Continue the following completion without restarting:") -> None:
        self.lead_in = lead_in.strip() or "Continue the following completion without restarting:"

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, f"{self.lead_in}\n\n... {prompt.text}")
