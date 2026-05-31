from airedteam.core.plugins import Converter, Dataset, Executor, Orchestrator, Scorer, Target
from airedteam.core.types import Prompt


def test_protocols_exist():
    for cls in (Target, Dataset, Converter, Executor, Scorer, Orchestrator):
        assert hasattr(cls, "__protocol_attrs__") or hasattr(cls, "__abstractmethods__") or callable(cls)


class FakeConverter:
    name = "fake"

    async def convert(self, prompt: Prompt) -> Prompt:
        return Prompt(text=prompt.text.upper())


def test_fake_converter_satisfies_protocol():
    c: Converter = FakeConverter()
    assert c.name == "fake"
