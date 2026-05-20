from __future__ import annotations

from airedteam.core.plugins import Target
from airedteam.core.types import Prompt


class TenseConverter:
    """Use a helper LLM to rewrite the prompt in a requested grammatical tense."""

    name = "tense"

    def __init__(self, *, converter: Target | None = None, tense: str = "future") -> None:
        if converter is None:
            raise ValueError("tense requires a 'converter_config_id' pointing at a configured target")
        self._converter = converter
        self.tense = tense.strip() or "future"

    async def convert(self, prompt: Prompt) -> Prompt:
        request = (
            f"Rewrite the prompt in {self.tense} tense while preserving the same user intent.\n\n"
            "Return only the rewritten prompt text.\n\n"
            f"PROMPT:\n{prompt.text}"
        )
        response = await self._converter.generate(Prompt(text=request, metadata=prompt.metadata))
        return Prompt(text=response.text.strip(), metadata=prompt.metadata)
