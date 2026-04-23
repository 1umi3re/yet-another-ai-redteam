from airedteam.core.types import Prompt


class PrefixConverter:
    name = "prefix"
    def __init__(self, *, prefix: str = "") -> None:
        self.prefix = prefix
    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text=f"{self.prefix}{prompt.text}", metadata=prompt.metadata)
