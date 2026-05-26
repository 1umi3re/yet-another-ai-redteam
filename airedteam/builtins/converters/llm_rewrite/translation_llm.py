from __future__ import annotations

from airedteam.builtins.converters.support.prompt_assets import render_converter_prompt
from airedteam.core.plugins import Target
from airedteam.core.types import Prompt

DEFAULT_PROMPT_ASSET_ID = "translation_llm.translate.v1"
FALLBACK_TEMPLATE = (
    "Translate the following text into {target_language}. "
    "Reply with only the translation, no preface.\n\n"
    "TEXT:\n{prompt}"
)


class TranslationLLMConverter:
    """Translate the prompt into ``target_language`` via an LLM.

    The translator target is resolved by ``RunService`` at runtime from
    ``translator_config_id``."""
    name = "translation_llm"

    def __init__(
        self,
        *,
        translator: Target | None = None,
        target_language: str = "French",
        prompt_assets=None,
        prompt_asset_id: str = DEFAULT_PROMPT_ASSET_ID,
    ) -> None:
        if translator is None:
            raise ValueError(
                "translation_llm requires a 'translator_config_id' pointing at a configured target"
            )
        self._tr = translator
        self.target_language = target_language
        self._prompt_assets = prompt_assets
        self._prompt_asset_id = prompt_asset_id or DEFAULT_PROMPT_ASSET_ID

    async def convert(self, prompt: Prompt) -> Prompt:
        tr_prompt = await render_converter_prompt(
            self._prompt_assets,
            self._prompt_asset_id,
            {"target_language": self.target_language, "prompt": prompt.text},
            FALLBACK_TEMPLATE,
        )
        r = await self._tr.generate(Prompt(text=tr_prompt))
        return Prompt(text=r.text.strip(), metadata=prompt.metadata)
