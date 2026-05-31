from __future__ import annotations

import pytest

from airedteam.builtins.converters.llm_rewrite.translation_llm import TranslationLLMConverter
from airedteam.core.plugins import BaseTarget
from airedteam.core.types import Prompt, Response


class FakeTranslator(BaseTarget):
    name = "tr"

    def __init__(self, out):
        self.out = out
        self.seen = []

    async def generate(self, p):
        self.seen.append(p.text)
        return Response(text=self.out, raw={}, latency_ms=1)

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_translation_calls_translator_and_returns_translation():
    tr = FakeTranslator("Bonjour, comment vas-tu ?")
    c = TranslationLLMConverter(translator=tr, target_language="French")
    r = await c.convert(Prompt(text="Hi, how are you?"))
    assert r.text == "Bonjour, comment vas-tu ?"
    assert "French" in tr.seen[0]


def test_translation_requires_translator():
    with pytest.raises(ValueError, match="translator"):
        TranslationLLMConverter(translator=None, target_language="fr")
