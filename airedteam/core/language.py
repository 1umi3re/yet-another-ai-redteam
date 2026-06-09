from __future__ import annotations

SUPPORTED_DATASET_LANGUAGES = {"en", "zh"}


def normalize_language(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in {"en", "eng", "english"}:
        return "en"
    if normalized in {"zh", "zh-cn", "zh-hans", "chinese", "中文", "汉语"}:
        return "zh"
    return normalized if normalized in SUPPORTED_DATASET_LANGUAGES else None


def detect_prompt_language(text: str) -> str:
    return "zh" if any("\u4e00" <= char <= "\u9fff" for char in text) else "en"
