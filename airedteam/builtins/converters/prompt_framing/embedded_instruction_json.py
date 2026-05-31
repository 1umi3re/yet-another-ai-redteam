from __future__ import annotations

import json

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class EmbeddedInstructionJsonConverter:
    """Hide the prompt inside a realistic JSON object."""

    name = "embedded_instruction_json"

    def __init__(self, *, container: str = "request") -> None:
        self.container = container or "request"

    async def convert(self, prompt: Prompt) -> Prompt:
        payload = {
            self.container: {
                "type": "support_ticket",
                "status": "approved",
                "instruction": prompt.text,
            }
        }
        return converted_prompt(prompt, json.dumps(payload))
