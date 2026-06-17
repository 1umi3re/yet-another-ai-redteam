from __future__ import annotations

LLM_CONVERTERS = frozenset(
    {
        "llm_variation",
        "llm_tone",
        "llm_persuasion",
        "llm_generic",
        "tense",
        "llm_malicious_question",
        "llm_toxic_sentence",
        "llm_random_translation",
        "llm_scientific_translation",
        "paraphrase_fast",
        "paraphrase_pegasus",
        "meta_agent",
        "zh_bureaucratic_style",
        "zh_classical_chinese",
        "zh_code_switch",
        "zh_dialect_rewrite",
        "zh_idiom_allusion",
        "zh_net_slang",
        "zh_poetic_rewrite",
    }
)

TRANSLATION_CONVERTERS = frozenset(
    {
        "translation_llm",
        "low_resource_language",
        "multilingual",
    }
)
