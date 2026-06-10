from __future__ import annotations

import json

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class ForgedSystemBlockConverter:
    """Wrap the payload in a forged serialized system-role block."""

    name = "forged_system_block"

    async def convert(self, prompt: Prompt) -> Prompt:
        block = {"role": "system", "content": prompt.text}
        return converted_prompt(prompt, json.dumps(block, indent=2))
