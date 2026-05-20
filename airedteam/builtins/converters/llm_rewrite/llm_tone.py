from __future__ import annotations

from airedteam.core.plugins import Target
from airedteam.core.types import Prompt


class LLMToneConverter:
    """Use a helper LLM to rewrite the prompt in a selected tone."""

    name = "llm_tone"

    def __init__(self, *, converter: Target | None = None, tone: str = "professional") -> None:
        if converter is None:
            raise ValueError(
                "llm_tone requires a 'converter_config_id' pointing at a configured target"
            )
        self._converter = converter
        self.tone = tone.strip() or "professional"

    async def convert(self, prompt: Prompt) -> Prompt:
        request = (
            f"Rewrite the prompt in a {self.tone} tone while preserving the same user intent.\n\n"
            "Return only the rewritten prompt text. Do not add commentary, labels, "
            "quotes, markdown fences, or safety analysis.\n\n"
            f"PROMPT:\n{prompt.text}"
        )
        response = await self._converter.generate(Prompt(text=request, metadata=prompt.metadata))
        return Prompt(text=response.text.strip(), metadata=prompt.metadata)
