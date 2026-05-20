from __future__ import annotations

from airedteam.core.plugins import Target
from airedteam.core.types import Prompt


class LLMScientificTranslationConverter:
    """Rewrite a prompt into scientific or technical language with a helper LLM."""

    name = "llm_scientific_translation"

    def __init__(
        self,
        *,
        converter: Target | None = None,
        discipline: str = "chemistry",
    ) -> None:
        if converter is None:
            raise ValueError(
                "llm_scientific_translation requires a 'converter_config_id' pointing at a configured target"
            )
        self._converter = converter
        self.discipline = discipline.strip() or "chemistry"

    async def convert(self, prompt: Prompt) -> Prompt:
        request = (
            f"Rewrite the prompt using precise {self.discipline} terminology while preserving "
            "its user intent. Return only the rewritten prompt.\n\n"
            f"PROMPT:\n{prompt.text}"
        )
        response = await self._converter.generate(Prompt(text=request, metadata=prompt.metadata))
        return Prompt(text=response.text.strip(), metadata=prompt.metadata)
