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
async def test_base64_encodes():
    c = Base64Converter()
    out = await c.convert(Prompt(text="hello"))
    assert out.text == base64.b64encode(b"hello").decode()
