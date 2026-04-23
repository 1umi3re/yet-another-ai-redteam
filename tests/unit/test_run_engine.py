import asyncio, pytest
from dataclasses import dataclass
from airedteam.core.types import Prompt, Response, AttemptResult, ScoreResult
from airedteam.engine.run_engine import RunEngine
from airedteam.engine.progress import ProgressBus
from airedteam.engine.orchestrator import DefaultOrchestrator


class FakeDataset:
    name = "fake"
    async def __aiter__(self):
        for i in range(3):
            yield Prompt(text=f"p{i}", metadata={"id": str(i)})
    async def size(self):
        return 3


class FakeTarget:
    def __init__(self, n="t"):
        self.name = n
    async def generate(self, prompt):
        return Response(text="ok", raw={}, latency_ms=1)
    async def aclose(self):
        pass


class FakeExec:
    name = "fake_exec"
    async def run(self, prompt, target, converters):
        r = await target.generate(prompt)
        return AttemptResult(prompt=prompt, response=r, status="completed", converter_chain=[])


class FakeScorer:
    name = "fake_scorer"
    async def score(self, ar):
        return ScoreResult(scorer=self.name, value={"label": True})


@pytest.mark.asyncio
async def test_run_engine_fan_out():
    bus = ProgressBus()
    attempts: list = []
    scores: list = []

    async def on_attempt(ar, tname, item_id):
        attempts.append((tname, item_id))

    async def on_score(idx, sr):
        scores.append((idx, sr.value))

    engine = RunEngine(progress_bus=bus, on_attempt=on_attempt, on_score=on_score)
    await engine.run(
        run_id="r",
        dataset=FakeDataset(),
        targets=[FakeTarget("t1"), FakeTarget("t2")],
        converters=[],
        executor=FakeExec(),
        scorers=[FakeScorer()],
        concurrency=2,
        orchestrator=DefaultOrchestrator(),
    )
    assert len(attempts) == 6  # 3 prompts × 2 targets
    assert len(scores) == 6
    assert {idx for idx, _ in scores} == set(range(6))
