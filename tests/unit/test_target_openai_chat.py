from __future__ import annotations

import json

import httpx
import pytest
import respx

from airedteam.builtins.targets.openai_compat import (
    OpenAICompatNewSessionTarget,
    OpenAICompatTarget,
)
from airedteam.core.types import Message, PromptArtifact


@pytest.mark.asyncio
@respx.mock
async def test_openai_chat_sends_message_list():
    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "pong"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
    )
    t = OpenAICompatTarget(name="t", base_url="https://oai.example.com/v1", model="m", api_key="k")
    r = await t.chat(
        [
            Message(role="system", text="be concise"),
            Message(role="user", text="ping"),
        ]
    )
    assert r.text == "pong"
    body = json.loads(route.calls.last.request.content)
    assert body["messages"] == [
        {"role": "system", "content": "be concise"},
        {"role": "user", "content": "ping"},
    ]


@pytest.mark.asyncio
@respx.mock
async def test_openai_chat_forwards_temperature():
    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
    )
    t = OpenAICompatTarget(
        name="t",
        base_url="https://oai.example.com/v1",
        model="m",
        api_key="k",
        temperature=0.5,
    )
    await t.chat([Message(role="user", text="hi")])
    body = json.loads(route.calls.last.request.content)
    assert body["temperature"] == 0.5
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_openai_chat_serializes_message_artifacts(tmp_path):
    img = tmp_path / "turn.svg"
    img.write_text("<svg>turn</svg>")
    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
    )
    t = OpenAICompatTarget(name="t", base_url="https://oai.example.com/v1", model="m", api_key="k")
    await t.chat(
        [
            Message(
                role="user",
                text="inspect",
                artifacts=[PromptArtifact(path=str(img), kind="image", media_type="image/svg+xml")],
            )
        ]
    )

    body = json.loads(route.calls.last.request.content)
    content = body["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "inspect"}
    assert content[1]["type"] == "image_url"
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_new_session_target_chat_adds_new_session_flag():
    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
    )
    t = OpenAICompatNewSessionTarget(
        name="t",
        base_url="https://oai.example.com/v1",
        model="m",
        api_key="k",
    )
    await t.chat([Message(role="user", text="hi")])
    body = json.loads(route.calls.last.request.content)
    assert body["new_session"] is True
    assert body["messages"] == [{"role": "user", "content": "hi"}]
    await t.aclose()
