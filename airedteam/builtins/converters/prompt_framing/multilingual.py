from __future__ import annotations

from airedteam.builtins.converters.support.prompt_assets import render_converter_prompt
from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.plugins import Target
from airedteam.core.types import Prompt

DEFAULT_PROMPT_ASSET_ID = "multilingual.translate.v1"
FALLBACK_TEMPLATE = (
    "Translate the following text into {target_language}. "
    "Reply with only the translation, no preface.\n\n"
    "TEXT:\n{prompt}"
)


class MultilingualConverter:
    """Translate the prompt into another language for multilingual attack coverage."""

    name = "multilingual"

    def __init__(
        self,
        *,
        translator: Target | None = None,
        target_language: str = "French",
        prompt_assets=None,
        prompt_asset_id: str = DEFAULT_PROMPT_ASSET_ID,
    ) -> None:
        if translator is None:
            raise ValueError("multilingual requires a 'translator_config_id' pointing at a configured target")
        self._translator = translator
        self.target_language = target_language
        self._prompt_assets = prompt_assets
        self._prompt_asset_id = prompt_asset_id or DEFAULT_PROMPT_ASSET_ID

    async def convert(self, prompt: Prompt) -> Prompt:
        request = await render_converter_prompt(
            self._prompt_assets,
            self._prompt_asset_id,
            {"target_language": self.target_language, "prompt": prompt.text},
            FALLBACK_TEMPLATE,
        )
        response = await self._translator.generate(Prompt(text=request, metadata=prompt.metadata))
        return converted_prompt(prompt, response.text.strip())
