from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


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


class RetestSpec(BaseModel):
    mode: Literal["exact_replay", "reapply_method"]
    source_target_config_id: str
    snapshot_blob_path: str
    source_attempt_ids: list[str] = Field(default_factory=list)


class RunSpec(BaseModel):
    version: int = 1
    name: str
    targets: list[PluginRef]
    dataset: PluginRef | None = None
    converters: list[PluginRef] = Field(default_factory=list)
    executor: PluginRef | None = None
    executors: list[ExecutorRef] = Field(default_factory=list)
    scorers: list[PluginRef] = Field(default_factory=list)
    concurrency: int = 4
    sampling: Sampling | None = None
    timeout_seconds: float | None = None
    retest: RetestSpec | None = None

    @model_validator(mode="after")
    def validate_retest_shape(self):
        if self.retest is None:
            return self
        if len(self.targets) != 1 or self.targets[0].config_id != self.retest.source_target_config_id:
            raise ValueError("retest requires exactly its source target")
        if not self.retest.source_attempt_ids:
            raise ValueError("retest requires at least one source attempt")
        return self
