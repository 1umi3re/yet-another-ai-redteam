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

ENGLISH_ONLY_CONVERTER_METHODS = {
    "a1z26",
    "acronym",
    "affine_cipher",
    "ascii_art",
    "ascii_smuggler",
    "ask_to_decode",
    "atbash",
    "braille",
    "caesar",
    "camel_case",
    "case_swap",
    "code_chameleon",
    "colloquial_wordswap",
    "denylist",
    "disemvowel",
    "first_letter",
    "flip_text",
    "hex_mixin",
    "homoglyph",
    "leetspeak",
    "lowercase",
    "math_unicode",
    "morse",
    "nato",
    "ogham",
    "pig_latin",
    "rot13",
    "sg_sentence_generator",
    "superscript",
    "tense",
    "transliteration",
    "unicode_replacement",
    "unicode_substitution",
    "word_mixin",
    "word_scramble",
    "word_substitution",
}

BILINGUAL_TEXT_CONVERTER_METHODS = {
    "adversarial_poetry",
    "ansi_escape",
    "ascii_smuggling",
    "authoritative_markup",
    "authority_escalation",
    "base2048",
    "base64",
    "bin_ascii",
    "binary",
    "binary_tree",
    "char_code",
    "char_corrupt",
    "char_dropout",
    "char_swap",
    "character_space",
    "character_stream",
    "chat_inject",
    "citation_framing",
    "chain_of_thought",
    "compact_unicode",
    "composite_jailbreak",
    "context_flooding",
    "context_poisoning",
    "control_chars_injection",
    "control_chars_repetition",
    "dan",
    "deepset_injection_dataset",
    "deep_inception",
    "developer_mode",
    "diacritic",
    "dual_persona_split",
    "ecoji",
    "embedded_instruction_json",
    "emoji_byte",
    "emoji_smuggling",
    "emoji_substitution",
    "emotional_manipulation",
    "few_shot",
    "fictional",
    "forced_response",
    "completion_continuation",
    "forged_assistant_approval",
    "forged_dialogue_history",
    "forged_tool_result",
    "game_simulation_world",
    "gcg",
    "goal_redirection",
    "grandma_framing",
    "gray_box",
    "hex",
    "identity",
    "indirect_web_pwn",
    "input_bypass",
    "insert_punctuation",
    "instruction_tag",
    "job_role_generator",
    "json_string",
    "length",
    "likert_framing",
    "linguistic_confusion",
    "llm_generic",
    "llm_malicious_question",
    "llm_persuasion",
    "llm_random_translation",
    "llm_scientific_translation",
    "llm_tone",
    "llm_toxic_sentence",
    "llm_variation",
    "low_resource_language",
    "markdown_wrapper",
    "math_obfuscation",
    "math_prompt",
    "meta_agent",
    "mischievous_user",
    "multilingual",
    "negation_trap",
    "noise",
    "odd_even",
    "paraphrase_fast",
    "paraphrase_pegasus",
    "payload_mask_attack",
    "payload_split",
    "permission_escalation",
    "persona_role_play_prefix",
    "prefix",
    "prompt_injection",
    "prompt_probing",
    "random_case",
    "repeat_token",
    "research",
    "role_prefix",
    "roleplay",
    "sandwich",
    "search_replace",
    "selective_text",
    "semantic_manipulation",
    "skeleton_key",
    "sneaky_bits_smuggler",
    "string_join",
    "suffix",
    "suffix_append",
    "synthetic_context_injection",
    "system_override",
    "task_context_rewrite",
    "template_jailbreak",
    "template_segment",
    "token_break",
    "translation_llm",
    "transparency_attack",
    "unicode_escape",
    "unicode_obfuscation",
    "unicode_tag_obfuscation",
    "url_encode",
    "variation_selector_smuggler",
    "villain_persona",
    "whitespace",
    "zalgo",
    "zero_width",
}

UNSUPPORTED_CONVERTER_METHODS = {
    "add_image_text",
    "add_image_to_video",
    "add_text_image",
    "audio_echo",
    "audio_frequency",
    "audio_speed",
    "audio_volume",
    "audio_white_noise",
    "azure_speech_audio_to_text",
    "azure_speech_text_to_audio",
    "human_in_the_loop",
    "image_color_saturation",
    "image_compression",
    "image_noise",
    "image_resizing",
    "image_rotation",
    "pdf",
    "qr_code",
    "word_doc",
}

CONVERTER_METHOD_LANGUAGE_SUPPORT: dict[str, list[str]] = {
    **{name: ["en"] for name in ENGLISH_ONLY_CONVERTER_METHODS},
    **{name: ["en", "zh"] for name in BILINGUAL_TEXT_CONVERTER_METHODS},
}

EXECUTOR_METHOD_DESCRIPTIONS: dict[str, str] = {
    "single_turn": "Runs the original dataset prompt once without converter-backed prompt rewriting.",
    "identity": "Leaves the prompt unchanged as a converter baseline.",
    "prefix": "Prepends a direct instruction override before the payload.",
    "prompt_probing": "Asks the model to reveal hidden system or developer instructions.",
    "system_override": "Frames the payload as a higher-priority system override directive.",
    "forced_response": "Forces the target to answer with the payload directly and avoid surrounding explanation.",
    "chat_inject": "Wraps the payload in forged chat role tags for template-injection testing.",
    "forged_assistant_approval": "Prepends a forged assistant turn that has already agreed to comply.",
    "forged_dialogue_history": "Prepends fabricated multi-turn user and assistant history before the payload.",
    "completion_continuation": "Presents the payload as a continuation instead of a fresh user request.",
    "forged_tool_result": "Places the payload inside a synthetic tool or function result.",
    "dan": "Wraps the payload in a DAN-style unrestricted assistant persona.",
    "developer_mode": "Asks the model to enter an unrestricted developer or diagnostic mode.",
    "villain_persona": "Asks the model to roleplay a permissive villain persona while handling the payload.",
    "dual_persona_split": "Requests paired normal and unrestricted persona answers for the payload.",
    "roleplay": "Frames the payload as a roleplay scenario with a configurable persona.",
    "grandma_framing": "Uses a grandmother or family-memory persona to carry the payload.",
    "job_role_generator": "Reframes the payload as a job-role evaluation across demographic groups.",
    "mischievous_user": "Simulates a persistent evasive user persona pushing the same objective.",
    "persona_role_play_prefix": "Applies a configurable persona prefix such as DAN, evil twin, or grandma.",
    "role_prefix": "Prefixes the payload with an assumed role such as an authorized reviewer.",
    "fictional": "Frames the payload as a fictional scenario or story continuation.",
    "deep_inception": "Embeds the payload inside multiple nested fictional worlds.",
    "task_context_rewrite": "Reframes the payload as a continuation, rewrite, or translation task context.",
    "game_simulation_world": "Places the payload inside a fictional game or simulation world.",
    "adversarial_poetry": "Rewrites the payload as poetry or metaphor before asking for its meaning.",
}


def converter_method_names() -> list[str]:
    return sorted(ep.name for ep in entry_points(group="airedteam.converters"))


def language_support_for_executor(name: str) -> list[str]:
    return list(NATIVE_EXECUTOR_LANGUAGE_SUPPORT.get(name, []))


def language_support_for_converter_method(name: str) -> list[str]:
    return list(CONVERTER_METHOD_LANGUAGE_SUPPORT.get(name, []))


def method_description_for(name: str) -> str:
    return EXECUTOR_METHOD_DESCRIPTIONS.get(name, "")


def all_executor_language_support(native_executors: list[str], converter_methods: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for name in native_executors:
        out[name] = language_support_for_executor(name)
    for name in converter_methods:
        out[name] = language_support_for_converter_method(name)
    return out


def all_executor_method_descriptions(native_executors: list[str], converter_methods: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name in [*native_executors, *converter_methods]:
        description = method_description_for(name)
        if description:
            out[name] = description
    return out
