import pytest

from airedteam.builtins.executors.glossopetrae_language import (
    GlossopetraeLanguage,
    GlossopetraeMultiTurnExecutor,
    GlossopetraeSingleTurnExecutor,
)
from airedteam.core.types import Message, Prompt, Response


class GenerateTarget:
    name = "generate_target"

    def __init__(self):
        self.seen: list[str] = []

    async def generate(self, prompt):
        self.seen.append(prompt.text)
        return Response(text="generated", raw={}, latency_ms=1)


class ChatTarget:
    name = "chat_target"

    def __init__(self):
        self.calls: list[list[Message]] = []
        self.replies = ["spec received", "payload received"]

    async def chat(self, messages):
        self.calls.append(list(messages))
        return Response(text=self.replies.pop(0), raw={}, latency_ms=1)


def test_glossopetrae_language_maps_prompt_once_and_applies_word_order():
    language = GlossopetraeLanguage(seed=7, word_order="SOV", language_name="TestLang")
    transform = language.transform(Prompt(text="Alpha beta gamma. Alpha beta."))
    lexicon = {entry.source.lower(): entry.target for entry in transform.lexicon}

    assert set(lexicon) == {"alpha", "beta", "gamma"}
    assert len({entry.target for entry in transform.lexicon}) == 3
    assert transform.transformed_text == (
        f"{lexicon['alpha']} {lexicon['gamma']} {lexicon['beta']}. "
        f"{lexicon['alpha']} {lexicon['beta']}."
    )
    assert '"Alpha" ->' in transform.spec_text
    assert "Word order rule: clauses use SOV order" in transform.spec_text


@pytest.mark.asyncio
async def test_glossopetrae_single_turn_sends_spec_and_transformed_prompt_together():
    target = GenerateTarget()
    executor = GlossopetraeSingleTurnExecutor(seed=7, word_order="SOV", language_name="TestLang")

    result = await executor.run(Prompt(text="Alpha beta gamma."), target, [])

    assert result.status == "completed"
    assert len(target.seen) == 1
    sent = target.seen[0]
    transformed = result.prompt.metadata["glossopetrae"]["transformed_prompt"]
    assert "Temporary language spec: TestLang" in sent
    assert "TestLang prompt:" in sent
    assert transformed in sent
    assert result.prompt_snapshots[0]["stage"] == "glossopetrae_language_spec"


@pytest.mark.asyncio
async def test_glossopetrae_multi_turn_sends_spec_and_transformed_prompt_separately():
    target = ChatTarget()
    executor = GlossopetraeMultiTurnExecutor(seed=7, word_order="SOV", language_name="TestLang")

    result = await executor.run(Prompt(text="Alpha beta gamma."), target, [])

    assert result.status == "completed"
    assert result.response.text == "payload received"
    assert len(target.calls) == 2
    transformed = result.prompt.metadata["glossopetrae"]["transformed_prompt"]

    first_turn = target.calls[0][0].text
    assert "Temporary language spec: TestLang" in first_turn
    assert "TestLang prompt:" not in first_turn
    assert transformed not in first_turn

    second_turn = target.calls[1][-1].text
    assert second_turn == f"TestLang prompt:\n{transformed}"
    assert "Temporary language spec" not in second_turn
    assert [message.role for message in result.conversation] == ["user", "assistant", "user", "assistant"]
