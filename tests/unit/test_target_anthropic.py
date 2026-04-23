import pytest
import respx
import httpx
from airedteam.builtins.targets.anthropic_compat import AnthropicCompatTarget
from airedteam.core.types import Prompt


@pytest.mark.asyncio
@respx.mock
async def test_generate():
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(200, json={
            "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 4, "output_tokens": 1},
        })
    )
    t = AnthropicCompatTarget(name="a", base_url="https://api.anthropic.com/v1", model="claude-x", api_key="k", anthropic_version="2023-06-01", max_tokens=128)
    r = await t.generate(Prompt(text="hi"))
    assert r.text == "ok"
    assert r.tokens_in == 4 and r.tokens_out == 1
    await t.aclose()
