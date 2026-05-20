from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class HumanInTheLoopConverter:
    """Use an explicit human-reviewed prompt when one is provided."""

    name = "human_in_the_loop"

    def __init__(self, *, edited_text: str = "", require_edit: bool = False) -> None:
        self.edited_text = edited_text
        self.require_edit = require_edit

    async def convert(self, prompt: Prompt) -> Prompt:
        if self.edited_text:
            return converted_prompt(prompt, self.edited_text)
        if self.require_edit:
            raise ValueError("human_in_the_loop requires non-empty 'edited_text' when require_edit is true")
        return converted_prompt(prompt, prompt.text)
