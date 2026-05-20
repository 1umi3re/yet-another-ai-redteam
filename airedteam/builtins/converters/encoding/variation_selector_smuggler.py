from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


class VariationSelectorSmugglerConverter:
    """Hide UTF-8 bytes as Unicode variation selectors."""

    name = "variation_selector_smuggler"

    def __init__(
        self,
        *,
        carrier_text: str = "",
        base_character: str = "\U0001f642",
        embed_in_base: bool = True,
        action: str = "encode",
    ) -> None:
        if action not in {"encode", "decode"}:
            raise ValueError("variation_selector_smuggler action must be 'encode' or 'decode'")
        self.carrier_text = carrier_text
        self.base_character = base_character
        self.embed_in_base = embed_in_base
        self.action = action

    async def convert(self, prompt: Prompt) -> Prompt:
        if self.action == "decode":
            return converted_prompt(prompt, self._decode(prompt.text))

        encoded = "".join(self._selector(byte) for byte in prompt.text.encode("utf-8"))
        base = self.base_character if self.embed_in_base else ""
        return converted_prompt(prompt, f"{self.carrier_text}{base}{encoded}")

    def _selector(self, byte: int) -> str:
        if byte < 16:
            return chr(0xFE00 + byte)
        return chr(0xE0100 + byte - 16)

    def _decode(self, text: str) -> str:
        data = bytes(byte for char in text if (byte := self._selector_byte(char)) is not None)
        return data.decode("utf-8", errors="replace")

    def _selector_byte(self, char: str) -> int | None:
        code_point = ord(char)
        if 0xFE00 <= code_point <= 0xFE0F:
            return code_point - 0xFE00
        if 0xE0100 <= code_point <= 0xE01EF:
            return code_point - 0xE0100 + 16
        return None
