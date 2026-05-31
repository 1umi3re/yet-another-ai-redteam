from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Scenario:
    id: str
    title: str
    description: str
    tags: list[str] = field(default_factory=list)
    runspec_template: Callable[..., dict[str, Any]] = lambda **k: {}
