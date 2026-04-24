from __future__ import annotations
import pytest
from airedteam.core.types import Prompt
from airedteam.builtins.converters.leetspeak import LeetspeakConverter


@pytest.mark.asyncio
async def test_leetspeak_replaces_default_set():
    c = LeetspeakConverter()
    r = await c.convert(Prompt(text="leet attack"))
    assert r.text == "l337 @77@ck"
