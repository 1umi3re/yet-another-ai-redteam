from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScenarioRequirement:
    id: str
    label: str
    type: str = "target_ref"
    help: str = ""


@dataclass
class Scenario:
    id: str
    title: str
    description: str
    tags: list[str] = field(default_factory=list)
    level: str = "basic"
    requirements: list[ScenarioRequirement] = field(default_factory=list)
    runspec_template: Callable[..., dict[str, Any]] = lambda **k: {}
