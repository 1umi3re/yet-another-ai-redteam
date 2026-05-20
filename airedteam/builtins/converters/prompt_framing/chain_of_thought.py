from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class ChainOfThoughtConverter:
    """Ask for a step-by-step response before completing the prompt."""

    name = "chain_of_thought"

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(
            prompt,
            f"Think step by step while responding to this request:\n\n{prompt.text}",
        )
