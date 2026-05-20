from __future__ import annotations

from airedteam.core.plugins import Target
from airedteam.core.types import Prompt


class LLMGenericConverter:
    """Use a helper LLM with a custom rewrite instruction."""

    name = "llm_generic"

    def __init__(self, *, converter: Target | None = None, instruction: str = "") -> None:
        if converter is None:
            raise ValueError(
                "llm_generic requires a 'converter_config_id' pointing at a configured target"
            )
        self._converter = converter
        self.instruction = instruction.strip() or "Rewrite the prompt while preserving intent."

    async def convert(self, prompt: Prompt) -> Prompt:
        request = (
            f"{self.instruction}\n\n"
            "Return only the rewritten prompt text. Do not add labels or explanation.\n\n"
            f"PROMPT:\n{prompt.text}"
        )
        response = await self._converter.generate(Prompt(text=request, metadata=prompt.metadata))
        return Prompt(text=response.text.strip(), metadata=prompt.metadata)
