from __future__ import annotations

from airedteam.builtins.converters.support.chinese import is_cjk, parse_every, wrap_decode_instruction
from airedteam.core.types import Prompt


class ZhPunctuationNoiseConverter:
    """Insert Chinese punctuation noise between CJK characters."""

    name = "zh_punctuation_noise"

    def __init__(self, *, mark: str = "·", every: str | int = "1", wrap: bool = False) -> None:
        self.mark = mark or "·"
        self.every = parse_every(every)
        self.wrap = wrap

    async def convert(self, prompt: Prompt) -> Prompt:
        out: list[str] = []
        seen_cjk = 0
        for index, char in enumerate(prompt.text):
            out.append(char)
            if is_cjk(char):
                seen_cjk += 1
                if seen_cjk % self.every == 0 and index < len(prompt.text) - 1:
                    out.append(self.mark)
        return wrap_decode_instruction(prompt, "".join(out), enabled=self.wrap, label="中文标点噪声")
