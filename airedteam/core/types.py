from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal


MessageRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class Message:
    role: MessageRole
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Prompt:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


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
    conversation: list[Message] | None = None
    prompt_snapshots: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ScoreResult:
    scorer: str
    value: Any
    rationale: str | None = None
    prompt_snapshot: dict[str, Any] | None = None
