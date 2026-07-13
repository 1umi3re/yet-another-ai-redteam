from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

MessageRole = Literal["system", "user", "assistant"]
PromptArtifactKind = Literal["image", "audio", "video", "binary"]


@dataclass(frozen=True)
class PromptArtifact:
    path: str
    kind: PromptArtifactKind
    media_type: str
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Message:
    role: MessageRole
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    artifacts: list[PromptArtifact] = field(default_factory=list)


@dataclass(frozen=True)
class Prompt:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    artifacts: list[PromptArtifact] = field(default_factory=list)


@dataclass(frozen=True)
class Response:
    text: str
    raw: dict[str, Any]
    latency_ms: int
    tokens_in: int | None = None
    tokens_out: int | None = None


AttemptStatus = Literal["completed", "failed", "skipped"]


@dataclass
class AttemptResult:
    prompt: Prompt
    response: Response | None = None
    status: AttemptStatus = "completed"
    error: str | None = None
    converter_chain: list[str] = field(default_factory=list)
    executor_name: str | None = None
    executor_kind: str | None = None
    dataset_item_language: str | None = None
    conversation: list[Message] | None = None
    prompt_snapshots: list[dict[str, Any]] = field(default_factory=list)
    service_context: dict[str, Any] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    target_config_id: str | None = None
    executor_ref: dict[str, Any] | None = None
    source_run_id: str | None = None
    source_attempt_id: str | None = None
    retest_mode: str | None = None


@dataclass
class ScoreResult:
    scorer: str
    value: Any
    rationale: str | None = None
    prompt_snapshot: dict[str, Any] | None = None
