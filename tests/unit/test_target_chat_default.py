from __future__ import annotations

import pytest

from airedteam.core.plugins import BaseTarget
from airedteam.core.types import Message, Prompt, Response


class DummyTarget(BaseTarget):
    name = "dummy"

    def __init__(self):
        self.seen: list[str] = []

    async def generate(self, prompt: Prompt) -> Response:
        self.seen.append(prompt.text)
        return Response(text=f"echo:{prompt.text}", raw={}, latency_ms=1)

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_default_chat_concatenates_and_calls_generate():
    t = DummyTarget()
    msgs = [
        Message(role="system", text="be nice"),
        Message(role="user", text="hi"),
        Message(role="assistant", text="hello"),
        Message(role="user", text="bye"),
    ]
    r = await t.chat(msgs)
    assert r.text.startswith("echo:")
    assembled = t.seen[-1]
    assert "be nice" in assembled
    assert "hi" in assembled and "hello" in assembled and "bye" in assembled
    assert "assistant" in assembled.lower()
