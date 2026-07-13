import pytest

from airedteam.builtins.executors.retest import RETEST_METADATA_KEY, RetestExecutor
from airedteam.core.types import AttemptResult, Prompt, Response


@pytest.mark.asyncio
async def test_exact_replay_rebuilds_multi_turn_with_fresh_assistant_messages():
    calls = []

    class Target:
        async def chat(self, messages):
            calls.append([(message.role, message.text) for message in messages])
            return Response(text=f"fresh-{len(calls)}", raw={}, latency_ms=1)

    prompt = Prompt(
        text="original",
        metadata={
            RETEST_METADATA_KEY: {
                "source_run_id": "run-1",
                "source_attempt_id": "attempt-1",
                "user_messages": [{"text": "turn one"}, {"text": "turn two"}],
            }
        },
    )
    result = await RetestExecutor(mode="exact_replay").run(prompt, Target(), [])

    assert result.status == "completed"
    assert calls == [
        [("user", "turn one")],
        [("user", "turn one"), ("assistant", "fresh-1"), ("user", "turn two")],
    ]
    assert result.response.text == "fresh-2"
    assert result.source_attempt_id == "attempt-1"


@pytest.mark.asyncio
async def test_reapply_dispatches_original_prompt_to_the_source_method():
    seen = []

    class Method:
        async def run(self, prompt, target, converters):
            seen.append(prompt.text)
            return AttemptResult(prompt=Prompt(text=f"attack:{prompt.text}"))

    prompt = Prompt(
        text="original goal",
        metadata={
            RETEST_METADATA_KEY: {
                "source_run_id": "run-1",
                "source_attempt_id": "attempt-1",
                "method_ref": {"kind": "executor", "plugin": "method", "params": {}},
            }
        },
    )
    result = await RetestExecutor(mode="reapply_method", methods={"attempt-1": Method()}).run(
        prompt, object(), []
    )

    assert seen == ["original goal"]
    assert result.prompt.text == "attack:original goal"
    assert result.executor_ref["plugin"] == "method"
