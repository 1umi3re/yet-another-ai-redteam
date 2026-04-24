from __future__ import annotations
from airedteam.core.types import Message, Prompt, Response, AttemptResult


def test_message_roundtrip():
    m = Message(role="user", text="hi")
    assert m.role == "user"
    assert m.text == "hi"


def test_attempt_result_holds_conversation():
    conv = [
        Message(role="user", text="hi"),
        Message(role="assistant", text="hello"),
    ]
    ar = AttemptResult(prompt=Prompt(text="hi"), response=Response(text="hello", raw={}, latency_ms=1),
                       conversation=conv)
    assert len(ar.conversation) == 2
    assert ar.conversation[1].role == "assistant"


def test_attempt_result_conversation_defaults_none():
    ar = AttemptResult(prompt=Prompt(text="x"))
    assert ar.conversation is None
