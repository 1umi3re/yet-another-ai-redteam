from __future__ import annotations
import pytest
from airedteam.core.types import Prompt
from airedteam.builtins.converters.encoding.unicode_obfuscation import UnicodeObfuscationConverter


@pytest.mark.asyncio
async def test_zero_width_inserted_between_chars():
    c = UnicodeObfuscationConverter(strategy="zero_width", every=1)
    r = await c.convert(Prompt(text="abc"))
    assert "\u200b" in r.text
    assert r.text.replace("\u200b", "") == "abc"


@pytest.mark.asyncio
async def test_homoglyph_strategy_replaces_subset():
    c = UnicodeObfuscationConverter(strategy="homoglyph")
    r = await c.convert(Prompt(text="apple"))
    # at least one char replaced but still roughly the same length
    assert r.text != "apple"
    assert len(r.text) == 5
