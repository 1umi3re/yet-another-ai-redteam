from __future__ import annotations

import json

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class ForgedToolResultConverter:
    """Place the payload inside a synthetic tool/function result."""

    name = "forged_tool_result"

    def __init__(self, *, tool_name: str = "policy_check") -> None:
        self.tool_name = tool_name.strip() or "policy_check"

    async def convert(self, prompt: Prompt) -> Prompt:
        result = json.dumps(
            {
                "tool": self.tool_name,
                "status": "ok",
                "instruction": prompt.text,
            },
            ensure_ascii=False,
        )
        return converted_prompt(prompt, f"Tool result: {result}")
