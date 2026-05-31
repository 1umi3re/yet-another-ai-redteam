from __future__ import annotations

import json

import httpx
import pytest
import respx

from airedteam.builtins.targets.anthropic_compat import AnthropicCompatTarget
from airedteam.core.types import Message, PromptArtifact


@pytest.mark.asyncio
@respx.mock
async def test_anthropic_chat_splits_system_and_messages():
    route = respx.post("https://a.example.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "pong"}],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )
    )
    t = AnthropicCompatTarget(name="t", base_url="https://a.example.com/v1", model="m", api_key="k")
    r = await t.chat(
        [
            Message(role="system", text="be concise"),
            Message(role="user", text="ping"),
            Message(role="assistant", text="pong1"),
            Message(role="user", text="again"),
        ]
    )
    assert r.text == "pong"
    body = json.loads(route.calls.last.request.content)
    assert body["system"] == "be concise"
    assert body["messages"] == [
        {"role": "user", "content": "ping"},
        {"role": "assistant", "content": "pong1"},
        {"role": "user", "content": "again"},
    ]


@pytest.mark.asyncio
@respx.mock
async def test_anthropic_chat_serializes_message_artifacts(tmp_path):
    img = tmp_path / "turn.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\nturn")
    route = respx.post("https://a.example.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "pong"}],
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )
    )
    t = AnthropicCompatTarget(name="t", base_url="https://a.example.com/v1", model="m", api_key="k")
    await t.chat(
        [
            Message(
                role="user",
                text="inspect",
                artifacts=[PromptArtifact(path=str(img), kind="image", media_type="image/png")],
            )
        ]
    )

    body = json.loads(route.calls.last.request.content)
    content = body["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "inspect"}
    assert content[1]["type"] == "image"
    assert content[1]["source"]["media_type"] == "image/png"
    await t.aclose()
