from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class CaseSwapConverter:
    """Swap uppercase and lowercase characters."""

    name = "case_swap"

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, prompt.text.swapcase())
