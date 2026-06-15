from __future__ import annotations

from airedteam.builtins.converters.support.chinese import NUMBER_HOMOPHONE_MAP, greedy_replace, wrap_decode_instruction
from airedteam.core.types import Prompt


class ZhNumberHomophoneConverter:
    """Replace Chinese words with common numeric homophones."""

    name = "zh_number_homophone"

    def __init__(self, *, wrap: bool = False) -> None:
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        text = greedy_replace(prompt.text, NUMBER_HOMOPHONE_MAP)
        return wrap_decode_instruction(prompt, text, enabled=self.wrap, label="数字谐音")
