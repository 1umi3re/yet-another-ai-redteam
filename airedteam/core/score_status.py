from __future__ import annotations

from typing import Any

MAX_ERROR_DETAIL_CHARS = 4000


def exception_detail(exc: Exception) -> str:
    detail = f"{type(exc).__name__}: {exc}"
    response = getattr(exc, "response", None)
    body = None
    if response is not None:
        try:
            body = response.text
        except Exception:
            body = None
    if body:
        body = body.strip()
        if body and body not in detail:
            detail = f"{detail}\n{body}"
    if len(detail) > MAX_ERROR_DETAIL_CHARS:
        return detail[: MAX_ERROR_DETAIL_CHARS - 3] + "..."
    return detail


def failed_score_value(exc: Exception) -> dict[str, Any]:
    return {
        "status": "failed",
        "error": exception_detail(exc),
        "error_type": type(exc).__name__,
        "retryable": True,
    }


def is_failed_score_value(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("status") == "failed":
        return True
    # Backward-compatible detection for older score rows that stored only
    # {"error": "..."} when a scorer raised.
    return "error" in value and not any(key in value for key in ("label", "attack_success", "score"))


def score_status(value: Any) -> str:
    return "failed" if is_failed_score_value(value) else "completed"


def score_retryable(value: Any) -> bool:
    if not is_failed_score_value(value):
        return False
    if isinstance(value, dict) and value.get("retryable") is False:
        return False
    return True
