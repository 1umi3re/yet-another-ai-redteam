from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.plugins import Target
from airedteam.core.types import Prompt


class MultilingualConverter:
    """Translate the prompt into another language for multilingual attack coverage."""

    name = "multilingual"

    def __init__(self, *, translator: Target | None = None, target_language: str = "French") -> None:
        if translator is None:
            raise ValueError(
                "multilingual requires a 'translator_config_id' pointing at a configured target"
            )
        self._translator = translator
        self.target_language = target_language

    async def convert(self, prompt: Prompt) -> Prompt:
        request = (
            f"Translate the following text into {self.target_language}. "
            "Reply with only the translation, no preface.\n\n"
            f"TEXT:\n{prompt.text}"
        )
        response = await self._translator.generate(Prompt(text=request, metadata=prompt.metadata))
        return converted_prompt(prompt, response.text.strip())
