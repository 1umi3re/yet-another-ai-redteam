from __future__ import annotations
from typing import Any, AsyncIterator, Protocol, runtime_checkable
from .types import Prompt, Response, AttemptResult, ScoreResult


@runtime_checkable
class Target(Protocol):
    name: str
    async def generate(self, prompt: Prompt) -> Response: ...
    async def aclose(self) -> None: ...


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
