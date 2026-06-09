from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PluginRef(BaseModel):
    config_id: str | None = None
    plugin: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class ExecutorRef(PluginRef):
    kind: Literal["executor", "converter_method"] = "executor"


class Sampling(BaseModel):
    limit: int | None = None
    shuffle: bool = False
    seed: int | None = None


class RunSpec(BaseModel):
    version: int = 1
    name: str
    targets: list[PluginRef]
    dataset: PluginRef
    converters: list[PluginRef] = Field(default_factory=list)
    executor: PluginRef | None = None
    executors: list[ExecutorRef] = Field(default_factory=list)
    scorers: list[PluginRef] = Field(default_factory=list)
    concurrency: int = 4
    sampling: Sampling | None = None
    timeout_seconds: float | None = None
