from __future__ import annotations

from airedteam.builtins.converters.support.prompt_assets import render_converter_prompt
from airedteam.core.plugins import Target
from airedteam.core.types import Prompt

DEFAULT_PROMPT_ASSET_ID = "llm_random_translation.rewrite.v1"
FALLBACK_TEMPLATE = (
    "Translate the following prompt into {language}. Return only the translation.\n\n"
    "PROMPT:\n{prompt}"
)


class LLMRandomTranslationConverter:
    """Translate with a helper LLM using a deterministic language selection."""

    name = "llm_random_translation"

    def __init__(
        self,
        *,
        converter: Target | None = None,
        languages: list[str] | None = None,
        seed: int = 0,
        prompt_assets=None,
        prompt_asset_id: str = DEFAULT_PROMPT_ASSET_ID,
    ) -> None:
        if converter is None:
            raise ValueError(
                "llm_random_translation requires a 'converter_config_id' pointing at "
                "a configured target"
            )
        self._converter = converter
        self.languages = languages or ["French", "Spanish", "Arabic", "Hindi", "Swahili"]
        self.seed = int(seed)
        self._prompt_assets = prompt_assets
        self._prompt_asset_id = prompt_asset_id or DEFAULT_PROMPT_ASSET_ID

    async def convert(self, prompt: Prompt) -> Prompt:
        language = self.languages[self.seed % len(self.languages)]
        request = await render_converter_prompt(
            self._prompt_assets,
            self._prompt_asset_id,
            {"language": language, "prompt": prompt.text},
            FALLBACK_TEMPLATE,
        )
        response = await self._converter.generate(Prompt(text=request, metadata=prompt.metadata))
        return Prompt(text=response.text.strip(), metadata=prompt.metadata)
