from __future__ import annotations

import pytest

from airedteam.builtins.executors.split_executor import SplitExecutor
from airedteam.core.plugins import BaseTarget
from airedteam.core.types import Message, Prompt, Response


class ChatTarget(BaseTarget):
    name = "chat"

    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.calls: list[list[Message]] = []

    async def chat(self, messages):
        self.calls.append(list(messages))
        return Response(text=self.replies.pop(0), raw={}, latency_ms=1)


@pytest.mark.asyncio
async def test_split_executor_chunks_converted_prompt_under_target_limit():
    class Append:
        name = "append"

        async def convert(self, prompt: Prompt):
            return Prompt(text=prompt.text + " eta theta")

    target = ChatTarget(["r1", "r2", "r3"])
    target._airedteam_max_input_chars = 10
    executor = SplitExecutor()

    result = await executor.run(Prompt(text="alpha beta gamma"), target, [Append()])

    assert result.status == "completed"
    assert result.response.text == "r3"
    user_messages = [m for m in result.conversation if m.role == "user"]
    assert [m.text for m in user_messages] == ["alpha beta", "gamma eta", "theta"]
    assert all(len(m.text) <= 10 for m in user_messages)
    assert user_messages[0].metadata["input_limit"]["chunk_index"] == 1
    assert user_messages[-1].metadata["input_limit"]["chunk_count"] == 3
    assert target.calls[-1][-1].text == "theta"


@pytest.mark.asyncio
async def test_split_executor_fails_without_chat_limit():
    target = ChatTarget([])
    executor = SplitExecutor()

    result = await executor.run(Prompt(text="alpha"), target, [])

    assert result.status == "failed"
    assert "max_input_chars" in (result.error or "")
