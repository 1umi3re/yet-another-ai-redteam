import pytest

from airedteam.core.types import Prompt
from airedteam.engine.orchestrator import DefaultOrchestrator


class FakeDataset:
    name = "fd"

    def __init__(self, items):
        self.items = items

    async def __aiter__(self):
        for t in self.items:
            yield Prompt(text=t)

    async def size(self):
        return len(self.items)


@pytest.mark.asyncio
async def test_yields_attempts_per_target_per_prompt():
    orch = DefaultOrchestrator()
    items = [p async for p in orch.attempts(FakeDataset(["a", "b"]), [])]
    assert [p.text for p in items] == ["a", "b"]
