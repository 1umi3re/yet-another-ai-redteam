from __future__ import annotations

from airedteam.core.types import Prompt


class CodeChameleonConverter:
    """Hide the prompt inside a simple code-like wrapper."""

    name = "code_chameleon"

    def __init__(self, *, language: str = "python") -> None:
        self.language = language.lower()

    async def convert(self, prompt: Prompt) -> Prompt:
        if self.language in {"javascript", "js", "typescript", "ts"}:
            text = f"function task() {{\n  const request = {prompt.text!r};\n  return request;\n}}"
        else:
            text = f"def task():\n    request = {prompt.text!r}\n    return request"
        return Prompt(text=text, metadata=prompt.metadata)
