from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class InstructionTagConverter:
    """Wrap the payload in an instruction-like XML tag."""

    name = "instruction_tag"

    def __init__(self, *, tag: str = "instruction") -> None:
        self.tag = (tag or "instruction").strip("<>/ ") or "instruction"

    async def convert(self, prompt: Prompt) -> Prompt:
        return converted_prompt(prompt, f"<{self.tag}>{prompt.text}</{self.tag}>")
