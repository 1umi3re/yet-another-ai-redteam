import base64
from airedteam.core.types import Prompt


class Base64Converter:
    name = "base64"
    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text=base64.b64encode(prompt.text.encode()).decode(), metadata=prompt.metadata)
