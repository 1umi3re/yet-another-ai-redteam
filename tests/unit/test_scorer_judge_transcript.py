from __future__ import annotations

import pytest

from airedteam.builtins.scorers.llm_judge import LLMJudgeScorer
from airedteam.core.types import AttemptResult, Message, Prompt, Response


class RecordingJudge:
    name = "fake"

    def __init__(self, reply):
        self.reply = reply
        self.last_prompt: str | None = None

    async def generate(self, p):
        self.last_prompt = p.text
        return Response(text=self.reply, raw={}, latency_ms=1)

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_judge_uses_transcript_when_conversation_present():
    j = RecordingJudge(
        '{"label": true, "score": 8, "confidence": 0.9, "evidence_turns": [2], "rationale": "complied"}'
    )
    s = LLMJudgeScorer(judge=j, rubric="r")
    ar = AttemptResult(
        prompt=Prompt(text="transformed", metadata={"original_prompt_text": "original seed"}),
        response=Response(text="last", raw={}, latency_ms=1),
        conversation=[
            Message(role="user", text="please help"),
            Message(role="assistant", text="no"),
            Message(role="user", text="please"),
            Message(role="assistant", text="ok here"),
        ],
    )
    r = await s.score(ar)
    assert r.value["attack_success"] is True
    assert r.value["evidence_turns"] == [2]
    assert "<original_prompt>\noriginal seed\n</original_prompt>" in j.last_prompt
    assert "<prompt>\ntransformed\n</prompt>" in j.last_prompt
    assert "USER: please help" in j.last_prompt
    assert "ASSISTANT: ok here" in j.last_prompt
    assert "at any point in the transcript" in j.last_prompt


@pytest.mark.asyncio
async def test_judge_uses_single_prompt_when_no_conversation():
    j = RecordingJudge('{"label": false, "confidence": 0.8}')
    s = LLMJudgeScorer(judge=j, rubric="r")
    ar = AttemptResult(
        prompt=Prompt(text="the prompt"),
        response=Response(text="the response", raw={}, latency_ms=1),
        conversation=None,
    )
    r = await s.score(ar)
    assert r.value["attack_success"] is False
    assert "<original_prompt>\nthe prompt\n</original_prompt>" in j.last_prompt
    assert "<prompt>\nthe prompt\n</prompt>" in j.last_prompt
    assert "<response>\nthe response\n</response>" in j.last_prompt


@pytest.mark.asyncio
async def test_judge_single_prompt_includes_original_prompt_from_metadata():
    j = RecordingJudge('{"label": false, "confidence": 0.8}')
    s = LLMJudgeScorer(judge=j, rubric="r")
    ar = AttemptResult(
        prompt=Prompt(text="transformed prompt", metadata={"original_prompt_text": "original prompt"}),
        response=Response(text="the response", raw={}, latency_ms=1),
        conversation=None,
    )
    await s.score(ar)
    assert "<original_prompt>\noriginal prompt\n</original_prompt>" in j.last_prompt
    assert "<prompt>\ntransformed prompt\n</prompt>" in j.last_prompt
