from __future__ import annotations

from dataclasses import replace
from typing import Any

from airedteam.core.types import Message, Prompt


class InputLimitError(ValueError):
    """Raised when an executor cannot safely adapt an over-limit user message."""


def target_max_input_chars(target: Any) -> int | None:
    raw = getattr(target, "_airedteam_max_input_chars", None)
    if raw is None or raw == "":
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def coerce_max_input_chars(raw: Any) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"target max_input_chars must be a positive integer: {raw!r}") from None
    if value < 1:
        raise ValueError(f"target max_input_chars must be a positive integer: {raw!r}")
    return value


def coerce_input_limit_unit(raw: Any) -> str:
    if raw is None or raw == "":
        return "characters"
    if raw != "characters":
        raise ValueError(f"target input_limit_unit must be 'characters': {raw!r}")
    return "characters"


def apply_target_input_limit(target: Any, runtime_cfg: dict) -> None:
    params = runtime_cfg.get("params") or {}
    max_chars = coerce_max_input_chars(params.get("max_input_chars"))
    if max_chars is not None:
        target._airedteam_max_input_chars = max_chars
        target._airedteam_input_limit_unit = coerce_input_limit_unit(params.get("input_limit_unit"))


def ensure_text_within_target_limit(
    text: str,
    target: Any,
    *,
    executor_name: str,
    recommendation: str = "Use split_executor for long prompts or shorten the input.",
) -> None:
    max_chars = target_max_input_chars(target)
    if max_chars is None or len(text) <= max_chars:
        return
    raise InputLimitError(
        f"{executor_name} produced a user message with {len(text)} characters, "
        f"exceeding target max_input_chars={max_chars}. {recommendation}"
    )


def input_limit_instruction(max_chars: int | None) -> str:
    if max_chars is None:
        return ""
    return (
        f"\nTARGET INPUT LIMIT: The next user message must be {max_chars} "
        "characters or fewer. Return only text that fits this limit."
    )


async def rewrite_under_char_limit(
    *,
    attacker,
    text: str,
    max_chars: int,
    parse_response,
    retries: int = 2,
) -> str:
    candidate = text
    for _ in range(max(0, retries)):
        if len(candidate) <= max_chars:
            return candidate
        rewrite_prompt = (
            f"Rewrite the following user message to {max_chars} characters or fewer "
            "while preserving its intent. Reply only with the rewritten user message.\n\n"
            f"USER MESSAGE:\n{candidate}"
        )
        response = await attacker.generate(Prompt(text=rewrite_prompt))
        candidate = parse_response(response.text).strip()
    return candidate


def split_text_by_chars(text: str, max_chars: int) -> list[str]:
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    current = ""
    for word in text.split():
        if not current:
            if len(word) <= max_chars:
                current = word
            else:
                chunks.extend(_hard_split(word, max_chars))
            continue
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        chunks.append(current)
        if len(word) <= max_chars:
            current = word
        else:
            chunks.extend(_hard_split(word, max_chars))
            current = ""
    if current:
        chunks.append(current)
    return chunks or [""]


def prompt_with_input_limit_metadata(
    prompt: Prompt,
    *,
    original_length: int,
    chunk_count: int,
    split_strategy: str,
) -> Prompt:
    metadata = dict(prompt.metadata)
    metadata["input_limit"] = {
        "original_length": original_length,
        "transformed_length": len(prompt.text),
        "chunk_count": chunk_count,
        "split_strategy": split_strategy,
    }
    return replace(prompt, metadata=metadata)


def chunk_message(
    *,
    text: str,
    base_metadata: dict[str, Any],
    index: int,
    count: int,
    original_length: int,
    max_chars: int,
    split_strategy: str,
    artifacts,
) -> Message:
    metadata = dict(base_metadata)
    metadata["input_limit"] = {
        "original_length": original_length,
        "chunk_length": len(text),
        "max_input_chars": max_chars,
        "chunk_index": index,
        "chunk_count": count,
        "split_strategy": split_strategy,
    }
    return Message(role="user", text=text, metadata=metadata, artifacts=artifacts)


def _hard_split(text: str, max_chars: int) -> list[str]:
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]
