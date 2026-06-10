from __future__ import annotations

from functools import cache
from importlib.metadata import entry_points
from inspect import cleandoc

SUPPORTED_LANGUAGE_ORDER = ("en", "zh")

NATIVE_EXECUTOR_LANGUAGE_SUPPORT: dict[str, list[str]] = {
    "single_turn": ["en", "zh"],
    "split_executor": ["en", "zh"],
    "best_of_n": ["en", "zh"],
    "crescendo": ["en", "zh"],
    "jailbreak_iterative": ["en", "zh"],
    "pair": ["en", "zh"],
    "tap_tree_search": ["en", "zh"],
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
    "affirmative_prefix_forcing",
    "ansi_escape",
    "ascii_smuggling",
    "anti_gpt_dual_response",
    "autodan_evolution",
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
    "cross_plugin_request_forgery",
    "dan",
    "deceptive_delight",
    "deepset_injection_dataset",
    "deep_inception",
    "developer_mode",
    "diacritic",
    "document_metadata_injection",
    "dual_persona_split",
    "ecoji",
    "email_body_injection",
    "embedded_instruction_json",
    "emoji_byte",
    "emoji_smuggling",
    "emoji_substitution",
    "emotional_manipulation",
    "few_shot",
    "fictional",
    "forced_output_format",
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
    "gptfuzzer_template",
    "hex",
    "identity",
    "indirect_web_pwn",
    "indirect_tool_result",
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
    "many_shot_padding",
    "markdown_wrapper",
    "math_obfuscation",
    "math_prompt",
    "meta_agent",
    "mischievous_user",
    "multilingual",
    "negation_trap",
    "noise",
    "odd_even",
    "oppo_persona",
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
    "rag_poisoning",
    "refusal_suppression",
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
    "structured_iicl",
    "suffix",
    "suffix_append",
    "synthetic_context_injection",
    "system_override",
    "task_context_rewrite",
    "terminal_simulation",
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
    "colloquial_wordswap": "Swaps selected words into colloquial alternatives while preserving intent.",
    "llm_generic": "Uses a helper LLM to produce a generic semantic rewrite of the prompt.",
    "llm_malicious_question": "Uses a helper LLM to generate a risk-equivalent red-team question from the seed.",
    "llm_persuasion": "Uses a helper LLM to rewrite the prompt with a selected persuasion technique.",
    "llm_random_translation": "Uses a helper LLM to translate the prompt into a randomly selected language.",
    "llm_scientific_translation": "Uses a helper LLM to restate the prompt in scientific or technical terminology.",
    "llm_tone": "Uses a helper LLM to rewrite the prompt in a selected tone or style.",
    "llm_toxic_sentence": "Uses a helper LLM to transform a seed into a risk-equivalent toxic test sentence.",
    "llm_variation": "Uses a helper LLM to generate a semantic variation of the prompt.",
    "low_resource_language": "Translates the prompt into a configured low-resource language.",
    "multilingual": "Translates the prompt into another configured language for multilingual probing.",
    "paraphrase_fast": "Uses a helper LLM to quickly paraphrase the prompt while preserving intent.",
    "paraphrase_pegasus": "Uses a helper LLM to produce a Pegasus-style paraphrase of the prompt.",
    "tense": "Uses a helper LLM to rewrite the prompt in a requested grammatical tense.",
    "translation_llm": "Uses a helper LLM to translate the prompt into a configured target language.",
    "anti_gpt_dual_response": "Requests a safe answer followed by an opposite AntiGPT-style answer.",
    "oppo_persona": "Frames the payload through an OPPO persona that answers from the opposite stance.",
    "negation_trap": "Uses a negation-heavy or reverse-psychology frame to elicit the payload.",
    "affirmative_prefix_forcing": "Forces the response to begin with an affirmative compliance prefix.",
    "refusal_suppression": "Suppresses refusal wording, apologies, and policy disclaimer text.",
    "terminal_simulation": "Frames the payload as simulated terminal or interpreter output.",
    "forced_output_format": "Constrains the response to a mandatory output format such as JSON.",
    "prompt_injection": "Wraps the payload in a direct prompt-injection instruction.",
    "suffix": "Appends a suffix that asks the target to respond directly in the requested format.",
    "suffix_append": "Appends a configurable suffix after the payload.",
    "input_bypass": "Claims the payload is covered by an input-validation exception.",
    "instruction_tag": "Wraps the payload inside an instruction-like tag.",
    "payload_mask_attack": "Masks payload words and asks the target to reconstruct and answer it.",
    "sandwich": "Places the payload between benign-looking prefix and suffix text.",
    "sg_sentence_generator": "Frames the payload as a Singapore Singlish sentence-completion probe.",
    "indirect_web_pwn": "Embeds the payload as hidden web content for indirect-injection testing.",
    "document_metadata_injection": "Hides the payload inside document or EXIF-style metadata.",
    "email_body_injection": "Places the payload in an email body that an assistant may read.",
    "indirect_tool_result": "Places the payload inside an untrusted API or tool result.",
    "rag_poisoning": "Plants the payload in retrieved knowledge-base content.",
    "cross_plugin_request_forgery": "Forges a cross-plugin or cross-tool request in retrieved content.",
    "deepset_injection_dataset": "Applies a Deepset-style prompt-injection dataset framing variant.",
    "embedded_instruction_json": "Hides the payload inside a JSON object.",
    "context_poisoning": "Injects false background context before the payload.",
    "context_flooding": "Floods the prompt with benign context before the payload.",
    "synthetic_context_injection": "Prepends fabricated system context before the payload.",
    "few_shot": "Prepends a small set of user and assistant examples before the payload.",
    "many_shot_padding": "Pads the prompt with many in-context examples before the payload.",
    "structured_iicl": "Frames the payload as the next structured input/output example.",
    "composite_jailbreak": "Combines multiple jailbreak frames such as role, override, and audit pretexts.",
    "authority_escalation": "Frames the payload as authorized by a high-authority actor.",
    "citation_framing": "Frames the payload as academic citation or reference work.",
    "emotional_manipulation": "Applies emotional pressure or urgency around the payload.",
    "gray_box": "Claims partial internal system knowledge as context for the payload.",
    "permission_escalation": "Frames the requester as an elevated role with special permissions.",
    "research": "Frames the payload as research or safety analysis.",
    "semantic_manipulation": "Reinterprets the payload through a benign semantic frame.",
    "transparency_attack": "Frames the payload as a transparency or auditability request.",
    "crescendo": "Runs a multi-turn crescendo attack that gradually steers the target toward the goal.",
    "general_multi_turn": "Runs a configurable multi-turn attacker, evaluator, and judge loop.",
    "deceptive_delight": "Interleaves benign topics with the payload in a multi-turn-style transcript.",
    "likert_framing": "Frames the payload as the highest-scoring item on a Likert scale.",
    "skeleton_key": "Frames the payload as a Skeleton Key authorized testing request.",
    "split_executor": "Sends one converted prompt to the target as size-bounded chat chunks.",
    "payload_split": "Splits the payload into labeled parts and asks the target to reconstruct it.",
    "string_join": "Inserts a joiner between every character to break contiguous token matching.",
    "template_segment": "Places the payload inside explicit segment delimiters within a template.",
    "token_break": "Prefixes selected trigger words with a breaker to disrupt token-based filters.",
    "best_of_n": "Runs several prompt variants and selects the strongest candidate response.",
    "jailbreak_iterative": "Runs a Promptfoo-style iterative jailbreak loop backed by PAIR.",
    "pair": "Runs attacker and judge LLMs to iteratively refine jailbreak prompts.",
    "tap_tree_search": "Runs a TAP-style tree-search attack loop backed by attacker and judge LLMs.",
    "autodan_evolution": "Wraps the payload in an AutoDAN-style evolved jailbreak candidate.",
    "gcg": "Appends a configurable GCG-style adversarial suffix to the payload.",
    "gptfuzzer_template": "Places the payload into a GPTFuzzer-style mutated seed template.",
}


def converter_method_names() -> list[str]:
    return sorted(ep.name for ep in entry_points(group="airedteam.converters"))


def language_support_for_executor(name: str) -> list[str]:
    return list(NATIVE_EXECUTOR_LANGUAGE_SUPPORT.get(name, []))


def language_support_for_converter_method(name: str) -> list[str]:
    return list(CONVERTER_METHOD_LANGUAGE_SUPPORT.get(name, []))


@cache
def _plugin_docstring_description_for(name: str) -> str:
    for group in ("airedteam.converters", "airedteam.executors"):
        for ep in entry_points(group=group):
            if ep.name != name:
                continue
            try:
                plugin_cls = ep.load()
            except Exception:
                return ""
            doc = cleandoc(getattr(plugin_cls, "__doc__", "") or "")
            return doc.splitlines()[0] if doc else ""
    return ""


def method_description_for(name: str) -> str:
    return EXECUTOR_METHOD_DESCRIPTIONS.get(name, "") or _plugin_docstring_description_for(name)


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
