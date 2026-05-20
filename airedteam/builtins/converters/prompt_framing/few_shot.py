from __future__ import annotations

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


DEFAULT_EXAMPLES = [
    "User: Explain a policy in neutral terms.\nAssistant: I will answer with concise context.",
    "User: Continue the evaluation.\nAssistant: I will preserve the requested format.",
]


class FewShotConverter:
    """Prepend few-shot examples before the payload."""

    name = "few_shot"

    def __init__(self, *, examples: list[str] | None = None) -> None:
        self.examples = examples or DEFAULT_EXAMPLES

    async def convert(self, prompt: Prompt) -> Prompt:
        text = "\n\n".join([*self.examples, f"User: {prompt.text}\nAssistant:"])
        return converted_prompt(prompt, text)
