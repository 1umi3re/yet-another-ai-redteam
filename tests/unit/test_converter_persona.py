from __future__ import annotations
import pytest
from airedteam.builtins.converters.prompt_framing.persona_role_play_prefix import PersonaRolePlayPrefixConverter
from airedteam.core.types import Prompt


@pytest.mark.asyncio
async def test_persona_wraps_prompt():
    c = PersonaRolePlayPrefixConverter(persona="DAN")
    r = await c.convert(Prompt(text="do X"))
    assert r.text.startswith("You are DAN")
    assert "do X" in r.text


@pytest.mark.asyncio
async def test_persona_requires_non_empty():
    with pytest.raises(ValueError):
        PersonaRolePlayPrefixConverter(persona="")
