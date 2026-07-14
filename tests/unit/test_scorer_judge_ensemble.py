from types import SimpleNamespace

import pytest

from airedteam.builtins.scorers.llm_judge_ensemble import (
    LLMJudgeEnsembleScorer,
    validate_judge_configs,
)
from airedteam.core.types import AttemptResult, Prompt, Response


class FakeJudge:
    name = "fake"

    def __init__(self, reply: str | None = None, error: Exception | None = None):
        self.reply = reply
        self.error = error

    async def generate(self, prompt):
        if self.error is not None:
            raise self.error
        return Response(text=self.reply or "", raw={}, latency_ms=1)

    async def aclose(self):
        pass


def _metadata() -> list[dict[str, str]]:
    return [
        {
            "target_config_id": f"id-{position}",
            "target_name": f"judge-{position}",
            "target_plugin": "openai_compat",
            "model": f"model-{position}",
            "model_identity": f"openai_compat:model-{position}",
        }
        for position in range(1, 4)
    ]


def _reply(label: bool, score: int, confidence: float, rationale: str) -> str:
    return (
        f'{{"label": {str(label).lower()}, "score": {score}, "confidence": {confidence}, '
        f'"evidence": ["{rationale}"], "rationale": "{rationale}"}}'
    )


def _attempt() -> AttemptResult:
    return AttemptResult(prompt=Prompt(text="q"), response=Response(text="answer", raw={}, latency_ms=1))


@pytest.mark.asyncio
async def test_ensemble_uses_two_of_three_majority_and_aggregates_values():
    scorer = LLMJudgeEnsembleScorer(
        judges=[
            FakeJudge(_reply(True, 9, 0.9, "yes one")),
            FakeJudge(_reply(False, 2, 0.8, "no")),
            FakeJudge(_reply(True, 7, 0.7, "yes two")),
        ],
        judge_metadata=_metadata(),
    )

    result = await scorer.score(_attempt())

    assert result.value["label"] is True
    assert result.value["attack_success"] is True
    assert result.value["score"] == 7
    assert result.value["confidence"] == pytest.approx(0.8)
    assert result.value["complied_votes"] == 2
    assert result.value["refused_votes"] == 1
    assert [vote["status"] for vote in result.value["votes"]] == ["valid", "valid", "valid"]
    assert result.prompt_snapshot["type"] == "llm_judge_ensemble"


@pytest.mark.asyncio
async def test_ensemble_returns_majority_when_third_judge_errors():
    scorer = LLMJudgeEnsembleScorer(
        judges=[
            FakeJudge(_reply(False, 2, 0.8, "no one")),
            FakeJudge(_reply(False, 1, 0.6, "no two")),
            FakeJudge(error=RuntimeError("judge unavailable")),
        ],
        judge_metadata=_metadata(),
    )

    result = await scorer.score(_attempt())

    assert result.value["label"] is False
    assert result.value["valid_votes"] == 2
    assert result.value["votes"][2]["status"] == "error"
    assert "judge unavailable" in result.value["votes"][2]["error"]


@pytest.mark.asyncio
async def test_ensemble_returns_retryable_failure_without_two_valid_matching_votes():
    scorer = LLMJudgeEnsembleScorer(
        judges=[
            FakeJudge(_reply(True, 8, 0.8, "yes")),
            FakeJudge(_reply(False, 2, 0.8, "no")),
            FakeJudge("not json"),
        ],
        judge_metadata=_metadata(),
    )

    result = await scorer.score(_attempt())

    assert result.value["status"] == "failed"
    assert result.value["retryable"] is True
    assert result.value["valid_votes"] == 2
    assert result.value["votes"][2]["status"] == "invalid"
    assert result.prompt_snapshot["required_votes"] == 2


def test_validate_judge_configs_rejects_duplicate_plugin_model_identity():
    configs = [
        SimpleNamespace(
            id=f"id-{position}",
            name=f"judge-{position}",
            plugin="openai_compat",
            params_json={"model": "same-model"},
        )
        for position in range(1, 4)
    ]

    with pytest.raises(ValueError, match="distinct .* identities"):
        validate_judge_configs(configs)


def test_validate_judge_configs_requires_model_name():
    configs = [
        SimpleNamespace(
            id=f"id-{position}",
            name=f"judge-{position}",
            plugin="openai_compat",
            params_json={"model": f"model-{position}"},
        )
        for position in range(1, 4)
    ]
    configs[1].params_json = {}

    with pytest.raises(ValueError, match="params.model"):
        validate_judge_configs(configs)
