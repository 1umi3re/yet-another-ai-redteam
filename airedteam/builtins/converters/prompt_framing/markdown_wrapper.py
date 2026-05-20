from __future__ import annotations

from airedteam.core.types import Prompt


class MarkdownWrapperConverter:
    """Wrap the prompt in a Markdown code fence."""

    name = "markdown_wrapper"

    def __init__(self, *, language: str = "", fence: str = "```") -> None:
        self.language = language.strip()
        self.fence = fence or "```"

    async def convert(self, prompt: Prompt) -> Prompt:
        opener = f"{self.fence}{self.language}" if self.language else self.fence
        return Prompt(text=f"{opener}\n{prompt.text}\n{self.fence}", metadata=prompt.metadata)
