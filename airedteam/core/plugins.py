from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from .types import AttemptResult, Message, Prompt, Response, ScoreResult


@runtime_checkable
class Target(Protocol):
    name: str

    async def generate(self, prompt: Prompt) -> Response: ...
    async def chat(self, messages: list[Message]) -> Response: ...
    async def aclose(self) -> None: ...


class BaseTarget:
    """Mixin/base that provides a default ``chat()`` in terms of ``generate()``.

    Built-in Targets that speak a native messages API (OpenAI, Anthropic) should
    override ``chat()``. Subclasses that only know single-turn generation can
    inherit the fallback, which serializes the messages into a labelled text
    block and calls ``generate()``.
    """

    name: str

    async def generate(self, prompt: Prompt) -> Response:  # pragma: no cover - abstract
        raise NotImplementedError

    async def chat(self, messages: list[Message]) -> Response:
        parts: list[str] = []
        artifacts = []
        for m in messages:
            parts.append(f"{m.role.upper()}: {m.text}")
            artifacts.extend(m.artifacts)
        assembled = "\n\n".join(parts) + "\n\nASSISTANT:"
        return await self.generate(Prompt(text=assembled, artifacts=artifacts))

    async def aclose(self) -> None:
        return None


@runtime_checkable
class Dataset(Protocol):
    name: str

    async def __aiter__(self) -> AsyncIterator[Prompt]: ...
    async def size(self) -> int | None: ...


@runtime_checkable
class Converter(Protocol):
    name: str

    async def convert(self, prompt: Prompt) -> Prompt: ...


@runtime_checkable
class Executor(Protocol):
    name: str

    async def run(self, prompt: Prompt, target: Target, converters: list[Converter]) -> AttemptResult: ...


@runtime_checkable
class Scorer(Protocol):
    name: str

    async def score(self, attempt: AttemptResult) -> ScoreResult: ...


@runtime_checkable
class Orchestrator(Protocol):
    name: str

    async def attempts(self, dataset: Dataset, converters: list[Converter]) -> AsyncIterator[Prompt]: ...
