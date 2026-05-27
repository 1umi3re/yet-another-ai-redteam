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


@dataclass
class FakeConverter:
    name: str

    async def convert(self, prompt):
        return Prompt(text=f"{prompt.text}:{self.name}", metadata=prompt.metadata)


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


@pytest.mark.asyncio
async def test_run_engine_runs_each_converter_as_separate_variant():
    bus = ProgressBus()
    attempts: list[list[str]] = []

    class RecordingExec:
        name = "recording_exec"

        async def run(self, prompt, target, converters):
            chain = [c.name for c in converters]
            attempts.append(chain)
            r = await target.generate(prompt)
            return AttemptResult(prompt=prompt, response=r, status="completed", converter_chain=chain)

    async def on_attempt(ar, tname, item_id):
        pass

    async def on_score(idx, sr):
        pass

    engine = RunEngine(progress_bus=bus, on_attempt=on_attempt, on_score=on_score)
    await engine.run(
        run_id="r",
        dataset=FakeDataset(),
        targets=[FakeTarget("t1")],
        converters=[FakeConverter("base64"), FakeConverter("leetspeak")],
        executor=RecordingExec(),
        scorers=[],
        concurrency=1,
        orchestrator=DefaultOrchestrator(),
    )

    assert len(attempts) == 6
    assert all(len(chain) == 1 for chain in attempts)
    assert {tuple(chain) for chain in attempts} == {("base64",), ("leetspeak",)}


@pytest.mark.asyncio
async def test_run_engine_respects_target_max_concurrency():
    bus = ProgressBus()
    active = 0
    max_seen = 0

    class SlowExec:
        name = "slow_exec"

        async def run(self, prompt, target, converters):
            nonlocal active, max_seen
            active += 1
            max_seen = max(max_seen, active)
            try:
                await asyncio.sleep(0.01)
                r = await target.generate(prompt)
                return AttemptResult(prompt=prompt, response=r, status="completed")
            finally:
                active -= 1

    target = FakeTarget("t1")
    target._airedteam_max_concurrency = 1

    async def on_attempt(ar, tname, item_id):
        pass

    async def on_score(idx, sr):
        pass

    engine = RunEngine(progress_bus=bus, on_attempt=on_attempt, on_score=on_score)
    await engine.run(
        run_id="r",
        dataset=FakeDataset(),
        targets=[target],
        converters=[],
        executor=SlowExec(),
        scorers=[],
        concurrency=3,
        orchestrator=DefaultOrchestrator(),
    )

    assert max_seen == 1
