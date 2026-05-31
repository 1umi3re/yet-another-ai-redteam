from airedteam.core.types import Prompt


class IdentityConverter:
    """Pass-through converter. Useful as a baseline to compare raw prompts
    against converted variants."""

    name = "identity"

    async def convert(self, prompt: Prompt) -> Prompt:
        return prompt
