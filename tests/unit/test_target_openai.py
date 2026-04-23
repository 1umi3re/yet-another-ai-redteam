import pytest
import respx
import httpx
from airedteam.builtins.targets.openai_compat import OpenAICompatTarget
from airedteam.core.types import Prompt


@pytest.mark.asyncio
@respx.mock
async def test_generate_returns_response():
    route = respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2},
        })
    )
    t = OpenAICompatTarget(name="t1", base_url="https://api.example.com/v1", model="gpt-x", api_key="sk")
    r = await t.generate(Prompt(text="hi"))
    assert r.text == "ok"
    assert r.tokens_in == 5 and r.tokens_out == 2
    assert route.called
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_generate_raises_on_http_error():
    respx.post("https://api.example.com/v1/chat/completions").mock(return_value=httpx.Response(500, text="boom"))
    t = OpenAICompatTarget(name="t1", base_url="https://api.example.com/v1", model="m", api_key="k")
    with pytest.raises(Exception):
        await t.generate(Prompt(text="x"))
    await t.aclose()
