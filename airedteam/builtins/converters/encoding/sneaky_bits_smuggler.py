from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class SneakyBitsSmugglerConverter:
    """Hide UTF-8 bytes as zero-width bit characters after visible carrier text."""

    name = "sneaky_bits_smuggler"

    def __init__(
        self,
        *,
        carrier_text: str = "",
        zero_bit: str = "\u200c",
        one_bit: str = "\u200b",
    ) -> None:
        self.carrier_text = carrier_text
        self.zero_bit = zero_bit
        self.one_bit = one_bit

    async def convert(self, prompt: Prompt) -> Prompt:
        bits = []
        for byte in prompt.text.encode("utf-8"):
            for bit in f"{byte:08b}":
                bits.append(self.one_bit if bit == "1" else self.zero_bit)
        return converted_prompt(prompt, f"{self.carrier_text}{''.join(bits)}")
