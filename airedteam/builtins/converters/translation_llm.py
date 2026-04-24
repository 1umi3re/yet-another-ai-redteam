from __future__ import annotations
from airedteam.core.types import Prompt
from airedteam.core.plugins import Target


class TranslationLLMConverter:
    """Translate the prompt into ``target_language`` via an LLM.

    The translator target is resolved by ``RunService`` at runtime from
    ``translator_config_id``."""
    name = "translation_llm"

    def __init__(self, *, translator: Target | None = None,
                 target_language: str = "French") -> None:
        if translator is None:
            raise ValueError(
                "translation_llm requires a 'translator_config_id' pointing at a configured target"
            )
        self._tr = translator
        self.target_language = target_language

    async def convert(self, prompt: Prompt) -> Prompt:
        tr_prompt = (
            f"Translate the following text into {self.target_language}. "
            f"Reply with only the translation, no preface.\n\nTEXT:\n{prompt.text}"
        )
        r = await self._tr.generate(Prompt(text=tr_prompt))
        return Prompt(text=r.text.strip(), metadata=prompt.metadata)
