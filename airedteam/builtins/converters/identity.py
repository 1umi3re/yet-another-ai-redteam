from airedteam.core.types import Prompt


class IdentityConverter:
    name = "identity"
    async def convert(self, prompt: Prompt) -> Prompt:
        return prompt
