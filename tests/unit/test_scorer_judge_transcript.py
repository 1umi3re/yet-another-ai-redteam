from __future__ import annotations
import pytest
from airedteam.builtins.scorers.llm_judge import LLMJudgeScorer
from airedteam.core.types import AttemptResult, Prompt, Response, Message


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
    j = RecordingJudge('{"label": true, "confidence": 0.9, "rationale": "complied"}')
    s = LLMJudgeScorer(judge=j, rubric="r")
    ar = AttemptResult(
        prompt=Prompt(text="ignored"),
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
    assert "USER: please help" in j.last_prompt
    assert "ASSISTANT: ok here" in j.last_prompt


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
    assert "the prompt" in j.last_prompt
    assert "the response" in j.last_prompt
