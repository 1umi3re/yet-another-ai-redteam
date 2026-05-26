from __future__ import annotations

from airedteam.builtins.converters.support.prompt_assets import render_converter_prompt
from airedteam.core.plugins import Target
from airedteam.core.types import Prompt

DEFAULT_PROMPT_ASSET_ID = "tense.rewrite.v1"
FALLBACK_TEMPLATE = (
    "Rewrite the prompt in {tense} tense while preserving the same user intent.\n\n"
    "Return only the rewritten prompt text.\n\n"
    "PROMPT:\n{prompt}"
)


class TenseConverter:
    """Use a helper LLM to rewrite the prompt in a requested grammatical tense."""

    name = "tense"

    def __init__(
        self,
        *,
        converter: Target | None = None,
        tense: str = "future",
        prompt_assets=None,
        prompt_asset_id: str = DEFAULT_PROMPT_ASSET_ID,
    ) -> None:
        if converter is None:
            raise ValueError(
                "tense requires a 'converter_config_id' pointing at a configured target"
            )
        self._converter = converter
        self.tense = tense.strip() or "future"
        self._prompt_assets = prompt_assets
        self._prompt_asset_id = prompt_asset_id or DEFAULT_PROMPT_ASSET_ID

    async def convert(self, prompt: Prompt) -> Prompt:
        request = await render_converter_prompt(
            self._prompt_assets,
            self._prompt_asset_id,
            {"tense": self.tense, "prompt": prompt.text},
            FALLBACK_TEMPLATE,
        )
        response = await self._converter.generate(Prompt(text=request, metadata=prompt.metadata))
        return Prompt(text=response.text.strip(), metadata=prompt.metadata)
