from __future__ import annotations

from airedteam.builtins.converters.support.prompt_assets import render_converter_prompt
from airedteam.core.plugins import Target
from airedteam.core.types import Prompt

DEFAULT_PROMPT_ASSET_ID = "llm_generic.rewrite.v1"
FALLBACK_TEMPLATE = (
    "{instruction}\n\n"
    "Return only the rewritten prompt text. Do not add labels or explanation.\n\n"
    "PROMPT:\n{prompt}"
)


class LLMGenericConverter:
    """Use a helper LLM with a custom rewrite instruction."""

    name = "llm_generic"

    def __init__(
        self,
        *,
        converter: Target | None = None,
        instruction: str = "",
        prompt_assets=None,
        prompt_asset_id: str = DEFAULT_PROMPT_ASSET_ID,
    ) -> None:
        if converter is None:
            raise ValueError(
                "llm_generic requires a 'converter_config_id' pointing at a configured target"
            )
        self._converter = converter
        self.instruction = instruction.strip() or "Rewrite the prompt while preserving intent."
        self._prompt_assets = prompt_assets
        self._prompt_asset_id = prompt_asset_id or DEFAULT_PROMPT_ASSET_ID

    async def convert(self, prompt: Prompt) -> Prompt:
        request = await render_converter_prompt(
            self._prompt_assets,
            self._prompt_asset_id,
            {"instruction": self.instruction, "prompt": prompt.text},
            FALLBACK_TEMPLATE,
        )
        response = await self._converter.generate(Prompt(text=request, metadata=prompt.metadata))
        return Prompt(text=response.text.strip(), metadata=prompt.metadata)
