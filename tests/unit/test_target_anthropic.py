import json
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


@pytest.mark.asyncio
@respx.mock
async def test_generate_preserves_system_prompt():
    route = respx.post("https://a.example.com/v1/messages").mock(
        return_value=httpx.Response(200, json={
            "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        })
    )
    t = AnthropicCompatTarget(
        name="t", base_url="https://a.example.com/v1", model="m", api_key="k",
        system_prompt="be safe", max_tokens=32,
    )
    await t.generate(Prompt(text="hi"))
    body = json.loads(route.calls.last.request.content)
    assert body["system"] == "be safe"
    assert body["max_tokens"] == 32
    assert body["messages"] == [{"role": "user", "content": "hi"}]
    await t.aclose()
