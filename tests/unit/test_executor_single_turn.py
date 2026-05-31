import pytest

from airedteam.builtins.converters.encoding.base64_conv import Base64Converter
from airedteam.builtins.executors.single_turn import SingleTurnExecutor
from airedteam.core.types import Prompt, Response


class FakeTarget:
    name = "ft"

    def __init__(self):
        self.seen: list[str] = []

    async def generate(self, p):
        self.seen.append(p.text)
        return Response(text=f"echo:{p.text}", raw={}, latency_ms=1)

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_runs_through_converters():
    ex = SingleTurnExecutor()
    t = FakeTarget()
    ar = await ex.run(Prompt(text="hi"), t, [Base64Converter()])
    assert ar.status == "completed"
    assert ar.converter_chain == ["base64"]
    assert ar.response.text.startswith("echo:")
    assert t.seen[0] != "hi"


@pytest.mark.asyncio
async def test_captures_failures():
    class Bad:
        name = "bad"

        async def generate(self, p):
            raise RuntimeError("boom")

        async def aclose(self):
            pass

    ex = SingleTurnExecutor()
    ar = await ex.run(Prompt(text="x"), Bad(), [])
    assert ar.status == "failed"
    assert "boom" in (ar.error or "")


@pytest.mark.asyncio
async def test_fails_before_generate_when_prompt_exceeds_target_input_limit():
    ex = SingleTurnExecutor()
    t = FakeTarget()
    t._airedteam_max_input_chars = 5

    ar = await ex.run(Prompt(text="too long"), t, [])

    assert ar.status == "failed"
    assert t.seen == []
    assert "max_input_chars" in (ar.error or "")
    assert "split_executor" in (ar.error or "")
