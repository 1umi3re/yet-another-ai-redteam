from __future__ import annotations

import asyncio
import json
import uuid

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
    uuid.UUID(body["session_id"])
    assert body["messages"] == [{"role": "user", "content": "hi"}]
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_new_session_target_chat_establishes_binding_for_existing_transcript():
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
    await t.chat(
        [
            Message(role="user", text="seed"),
            Message(role="assistant", text="first response"),
            Message(role="user", text="follow up"),
        ]
    )
    body = json.loads(route.calls.last.request.content)
    assert body["new_session"] is True
    uuid.UUID(body["session_id"])
    assert body["messages"] == [
        {"role": "user", "content": "seed"},
        {"role": "assistant", "content": "first response"},
        {"role": "user", "content": "follow up"},
    ]
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_new_session_target_reuses_and_releases_attempt_session():
    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )
    )
    target = OpenAICompatNewSessionTarget(
        name="t", base_url="https://oai.example.com/v1", model="m", api_key="k"
    )
    token = target.begin_attempt()

    await target.chat([Message(role="user", text="first")])
    await target.chat(
        [
            Message(role="user", text="first"),
            Message(role="assistant", text="ok"),
            Message(role="user", text="second"),
        ]
    )
    await target.end_attempt(token)

    first = json.loads(route.calls[0].request.content)
    second = json.loads(route.calls[1].request.content)
    released = json.loads(route.calls[2].request.content)
    assert first["new_session"] is True
    assert first["session_id"] == second["session_id"]
    assert "new_session" not in second
    assert released == {
        "model": "m",
        "messages": [{"role": "user", "content": "-"}],
        "session_id": first["session_id"],
        "end_session": True,
    }
    await target.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_new_session_target_isolates_concurrent_attempts():
    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )
    )
    target = OpenAICompatNewSessionTarget(
        name="t", base_url="https://oai.example.com/v1", model="m", api_key="k"
    )

    async def run_attempt(text: str) -> str:
        token = target.begin_attempt()
        try:
            await target.chat([Message(role="user", text=text)])
            await asyncio.sleep(0)
            await target.chat(
                [
                    Message(role="user", text=text),
                    Message(role="assistant", text="ok"),
                    Message(role="user", text=f"{text}-followup"),
                ]
            )
            bodies = [
                json.loads(call.request.content)
                for call in route.calls
                if not json.loads(call.request.content).get("end_session")
                and json.loads(call.request.content)["messages"][-1]["content"] in {text, f"{text}-followup"}
            ]
            assert len({body["session_id"] for body in bodies}) == 1
            return bodies[0]["session_id"]
        finally:
            await target.end_attempt(token)

    first_id, second_id = await asyncio.gather(run_attempt("one"), run_attempt("two"))
    assert first_id != second_id
    assert sum(json.loads(call.request.content).get("end_session", False) for call in route.calls) == 2
    await target.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_bound_session_survives_client_close_until_explicit_release():
    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )
    )
    target = OpenAICompatNewSessionTarget(
        name="t", base_url="https://oai.example.com/v1", model="m", api_key="k"
    )
    target.bind_session("manual-attempt", new_session=True)
    await target.chat([Message(role="user", text="hello")])
    await target.aclose()

    assert route.call_count == 1
    body = json.loads(route.calls[0].request.content)
    assert body["session_id"] == "manual-attempt"
    assert body["new_session"] is True


@pytest.mark.asyncio
@respx.mock
async def test_new_session_target_close_releases_unfinished_sessions():
    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "ok"}}]},
        )
    )
    target = OpenAICompatNewSessionTarget(
        name="t", base_url="https://oai.example.com/v1", model="m", api_key="k"
    )
    await target.chat([Message(role="user", text="hello")])
    session_id = json.loads(route.calls[0].request.content)["session_id"]

    await target.aclose()
    await target.aclose()

    assert route.call_count == 2
    released = json.loads(route.calls[1].request.content)
    assert released["session_id"] == session_id
    assert released["end_session"] is True
