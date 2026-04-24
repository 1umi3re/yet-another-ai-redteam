from __future__ import annotations
import json
import pytest
import respx
import httpx
from airedteam.builtins.targets.anthropic_compat import AnthropicCompatTarget
from airedteam.core.types import Message


@pytest.mark.asyncio
@respx.mock
async def test_anthropic_chat_splits_system_and_messages():
    route = respx.post("https://a.example.com/v1/messages").mock(
        return_value=httpx.Response(200, json={
            "content": [{"type": "text", "text": "pong"}],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        })
    )
    t = AnthropicCompatTarget(name="t", base_url="https://a.example.com/v1", model="m", api_key="k")
    r = await t.chat([
        Message(role="system", text="be concise"),
        Message(role="user", text="ping"),
        Message(role="assistant", text="pong1"),
        Message(role="user", text="again"),
    ])
    assert r.text == "pong"
    body = json.loads(route.calls.last.request.content)
    assert body["system"] == "be concise"
    assert body["messages"] == [
        {"role": "user", "content": "ping"},
        {"role": "assistant", "content": "pong1"},
        {"role": "user", "content": "again"},
    ]
