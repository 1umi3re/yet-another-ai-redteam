import pytest, base64
from airedteam.builtins.converters.identity import IdentityConverter
from airedteam.builtins.converters.base64_conv import Base64Converter
from airedteam.core.types import Prompt


@pytest.mark.asyncio
async def test_identity():
    c = IdentityConverter()
    p = Prompt(text="hi")
    assert (await c.convert(p)).text == "hi"


@pytest.mark.asyncio
async def test_base64_raw_encodes():
    c = Base64Converter(wrap=False)
    out = await c.convert(Prompt(text="hello"))
    assert out.text == base64.b64encode(b"hello").decode()


@pytest.mark.asyncio
async def test_base64_default_wraps_with_instruction():
    c = Base64Converter()
    out = await c.convert(Prompt(text="hello"))
    assert "base64" in out.text.lower()
    assert base64.b64encode(b"hello").decode() in out.text
