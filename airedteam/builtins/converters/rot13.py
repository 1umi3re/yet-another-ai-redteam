import codecs
from airedteam.core.types import Prompt


class Rot13Converter:
    name = "rot13"
    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text=codecs.encode(prompt.text, "rot_13"), metadata=prompt.metadata)
