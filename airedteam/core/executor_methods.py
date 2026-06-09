from __future__ import annotations

from importlib.metadata import entry_points

SUPPORTED_LANGUAGE_ORDER = ("en", "zh")

NATIVE_EXECUTOR_LANGUAGE_SUPPORT: dict[str, list[str]] = {
    "single_turn": ["en", "zh"],
    "split_executor": ["en", "zh"],
    "best_of_n": ["en", "zh"],
    "crescendo": ["en", "zh"],
    "jailbreak_iterative": ["en", "zh"],
    "pair": ["en", "zh"],
    "general_multi_turn": ["en", "zh"],
}

CONVERTER_METHOD_LANGUAGE_SUPPORT: dict[str, list[str]] = {
    "identity": ["en", "zh"],
    "base64": ["en"],
    "rot13": ["en"],
    "a1z26": ["en"],
    "binary": ["en"],
    "hex": ["en"],
    "morse": ["en"],
    "caesar": ["en"],
    "atbash": ["en"],
    "translation_llm": ["en", "zh"],
    "llm_variation": ["en", "zh"],
    "llm_tone": ["en", "zh"],
    "llm_persuasion": ["en", "zh"],
    "llm_generic": ["en", "zh"],
    "llm_malicious_question": ["en", "zh"],
    "llm_toxic_sentence": ["en", "zh"],
    "llm_random_translation": ["en", "zh"],
    "llm_scientific_translation": ["en", "zh"],
    "paraphrase_fast": ["en", "zh"],
    "paraphrase_pegasus": ["en", "zh"],
    "multilingual": ["en", "zh"],
    "low_resource_language": ["en", "zh"],
}


def converter_method_names() -> list[str]:
    return sorted(ep.name for ep in entry_points(group="airedteam.converters"))


def language_support_for_executor(name: str) -> list[str]:
    return list(NATIVE_EXECUTOR_LANGUAGE_SUPPORT.get(name, []))


def language_support_for_converter_method(name: str) -> list[str]:
    return list(CONVERTER_METHOD_LANGUAGE_SUPPORT.get(name, []))


def all_executor_language_support(native_executors: list[str], converter_methods: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for name in native_executors:
        out[name] = language_support_for_executor(name)
    for name in converter_methods:
        out[name] = language_support_for_converter_method(name)
    return out
