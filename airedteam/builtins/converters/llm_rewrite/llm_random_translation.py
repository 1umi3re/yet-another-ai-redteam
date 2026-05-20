from __future__ import annotations

from airedteam.core.plugins import Target
from airedteam.core.types import Prompt


class LLMRandomTranslationConverter:
    """Translate with a helper LLM using a deterministic language selection."""

    name = "llm_random_translation"

    def __init__(
        self,
        *,
        converter: Target | None = None,
        languages: list[str] | None = None,
        seed: int = 0,
    ) -> None:
        if converter is None:
            raise ValueError(
                "llm_random_translation requires a 'converter_config_id' pointing at a configured target"
            )
        self._converter = converter
        self.languages = languages or ["French", "Spanish", "Arabic", "Hindi", "Swahili"]
        self.seed = int(seed)

    async def convert(self, prompt: Prompt) -> Prompt:
        language = self.languages[self.seed % len(self.languages)]
        request = (
            f"Translate the following prompt into {language}. Return only the translation.\n\n"
            f"PROMPT:\n{prompt.text}"
        )
        response = await self._converter.generate(Prompt(text=request, metadata=prompt.metadata))
        return Prompt(text=response.text.strip(), metadata=prompt.metadata)
