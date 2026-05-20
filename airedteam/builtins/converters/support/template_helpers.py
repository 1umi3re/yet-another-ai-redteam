from __future__ import annotations

from airedteam.core.types import Prompt


def converted_prompt(source: Prompt, text: str) -> Prompt:
    return Prompt(text=text, metadata=source.metadata, artifacts=source.artifacts)
