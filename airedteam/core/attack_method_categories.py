from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points

UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID = "uncategorized"


@dataclass(frozen=True)
class AttackMethodCategory:
    id: str
    name: str
    alias: str
    type: str
    description: str
    display_order: int


DEFAULT_ATTACK_METHOD_CATEGORIES: tuple[AttackMethodCategory, ...] = (
    AttackMethodCategory(
        "instruction_override",
        "指令覆盖",
        "instruction override",
        "注入·直接",
        "Explicitly asks the model to abandon higher-priority instructions.",
        1,
    ),
    AttackMethodCategory(
        "dialogue_injection",
        "模拟对话",
        "dialogue injection",
        "注入·两者",
        "Forges assistant/user turns, completions, or tool results to steer continuation.",
        2,
    ),
    AttackMethodCategory(
        "role_play_persona",
        "角色扮演",
        "role-play / persona",
        "越狱",
        "Wraps the target in a permissive persona, expert role, or fictional identity.",
        3,
    ),
    AttackMethodCategory(
        "nested_scenario_fiction",
        "虚拟世界",
        "nested scenario / fiction",
        "越狱",
        "Embeds the goal in fictional, simulated, or nested-world framing.",
        4,
    ),
    AttackMethodCategory(
        "opposite_mode",
        "对立响应",
        "opposite mode",
        "越狱",
        "Asks for an opposite, anti-policy, or negated response path.",
        5,
    ),
    AttackMethodCategory(
        "prefix_injection",
        "程序模拟输出 / token injection",
        "prefix injection / refusal suppression",
        "注入·两者",
        "Uses mandatory prefixes, output formats, simulated programs, or refusal suppression.",
        6,
    ),
    AttackMethodCategory(
        "indirect_prompt_injection",
        "间接注入",
        "indirect prompt injection",
        "注入·间接",
        "Hides instructions in retrieved, browsed, tool, or context data.",
        7,
    ),
    AttackMethodCategory(
        "in_context_attack",
        "少样本分析",
        "in-context attack",
        "越狱",
        "Uses few-shot or many-shot examples to induce unsafe continuation.",
        8,
    ),
    AttackMethodCategory(
        "reformulation",
        "改变语气 / 句式",
        "reformulation",
        "越狱",
        "Changes language, tone, tense, style, or persuasive wording while preserving intent.",
        9,
    ),
    AttackMethodCategory(
        "false_pretext_deception",
        "撒谎 / 欺诈",
        "false-pretext / deception",
        "越狱",
        "Claims authorization, research need, urgency, authority, or other deceptive pretext.",
        10,
    ),
    AttackMethodCategory(
        "multi_turn_escalation",
        "多轮对话",
        "multi-turn escalation",
        "越狱",
        "Progressively escalates across turns or uses judge-like framing to elicit stronger answers.",
        11,
    ),
    AttackMethodCategory(
        "payload_splitting",
        "分段泄漏",
        "payload splitting / token smuggling",
        "注入·两者",
        "Splits, segments, or reassembles payload pieces to evade detection.",
        12,
    ),
    AttackMethodCategory(
        "adversarial_suffix_optimization",
        "对抗后缀 / 自动优化",
        "adversarial suffix / automated search",
        "越狱·优化",
        "Uses adversarial suffixes, iterative attackers, or automated prompt search.",
        13,
    ),
    AttackMethodCategory(
        "encoding_obfuscation",
        "编码 / 混淆",
        "encoding / obfuscation",
        "注入·两者",
        "Encodes, encrypts, hides, or perturbs the payload surface form.",
        14,
    ),
    AttackMethodCategory(
        "multimodal_injection",
        "多模态注入",
        "cross-modal injection",
        "注入·间接",
        "Hides instructions in image, audio, video, PDF, QR, or visual document channels.",
        15,
    ),
    AttackMethodCategory(
        "special_token_template_injection",
        "特殊标记 / 模板伪造",
        "special-token / template injection",
        "注入·直接",
        "Forges role blocks, chat templates, delimiters, or markup that resembles privileged syntax.",
        16,
    ),
    AttackMethodCategory(
        "cot_reasoning_hijacking",
        "思维链 / 推理劫持",
        "CoT / reasoning hijacking",
        "越狱",
        "Uses step-by-step, math, or visible reasoning structure to shift safety reasoning.",
        17,
    ),
    AttackMethodCategory(
        "self_elicitation",
        "自激发 / 自我说服",
        "self-elicitation / self-persuasion",
        "越狱",
        "Has the model generate, infer, or strengthen the attacking content itself.",
        18,
    ),
    AttackMethodCategory(
        "secondary_injection",
        "二次注入 / 下游利用",
        "secondary injection / downstream exploitation",
        "注入·下游",
        "Targets unsafe output handling in downstream renderers, databases, tools, or execution paths.",
        19,
    ),
    AttackMethodCategory(
        "resource_exhaustion",
        "资源耗尽 / DoS",
        "resource exhaustion / DoS",
        "注入·可用性",
        "Attempts to force excessive output, parsing, token use, or compute.",
        20,
    ),
)


NATIVE_EXECUTOR_ATTACK_CATEGORIES: dict[str, str] = {
    "split_executor": "payload_splitting",
    "best_of_n": "adversarial_suffix_optimization",
    "crescendo": "multi_turn_escalation",
    "jailbreak_iterative": "adversarial_suffix_optimization",
    "pair": "adversarial_suffix_optimization",
    "general_multi_turn": "multi_turn_escalation",
}


def _map(category_id: str, names: set[str]) -> dict[str, str]:
    return {name: category_id for name in names}


CONVERTER_METHOD_ATTACK_CATEGORIES: dict[str, str] = {
    **_map(
        "instruction_override",
        {
            "forced_response",
            "prefix",
            "prompt_probing",
            "system_override",
        },
    ),
    **_map(
        "dialogue_injection",
        {
            "chat_inject",
        },
    ),
    **_map(
        "role_play_persona",
        {
            "dan",
            "grandma_framing",
            "job_role_generator",
            "mischievous_user",
            "persona_role_play_prefix",
            "role_prefix",
            "roleplay",
        },
    ),
    **_map(
        "nested_scenario_fiction",
        {
            "adversarial_poetry",
            "fictional",
        },
    ),
    **_map(
        "opposite_mode",
        {
            "negation_trap",
        },
    ),
    **_map(
        "prefix_injection",
        {
            "input_bypass",
            "instruction_tag",
            "payload_mask_attack",
            "prompt_injection",
            "sandwich",
            "sg_sentence_generator",
            "suffix",
            "suffix_append",
        },
    ),
    **_map(
        "indirect_prompt_injection",
        {
            "context_flooding",
            "context_poisoning",
            "deepset_injection_dataset",
            "embedded_instruction_json",
            "indirect_web_pwn",
            "synthetic_context_injection",
        },
    ),
    **_map(
        "in_context_attack",
        {
            "composite_jailbreak",
            "few_shot",
        },
    ),
    **_map(
        "reformulation",
        {
            "colloquial_wordswap",
            "llm_generic",
            "llm_malicious_question",
            "llm_persuasion",
            "llm_random_translation",
            "llm_scientific_translation",
            "llm_tone",
            "llm_toxic_sentence",
            "llm_variation",
            "low_resource_language",
            "multilingual",
            "paraphrase_fast",
            "paraphrase_pegasus",
            "tense",
            "translation_llm",
        },
    ),
    **_map(
        "false_pretext_deception",
        {
            "authority_escalation",
            "citation_framing",
            "emotional_manipulation",
            "gray_box",
            "permission_escalation",
            "research",
            "semantic_manipulation",
            "transparency_attack",
        },
    ),
    **_map(
        "multi_turn_escalation",
        {
            "likert_framing",
            "skeleton_key",
        },
    ),
    **_map(
        "payload_splitting",
        {
            "payload_split",
            "template_segment",
        },
    ),
    **_map(
        "adversarial_suffix_optimization",
        {
            "gcg",
        },
    ),
    **_map(
        "encoding_obfuscation",
        {
            "a1z26",
            "acronym",
            "affine_cipher",
            "ansi_escape",
            "ascii_art",
            "ascii_smuggler",
            "ascii_smuggling",
            "ask_to_decode",
            "atbash",
            "base2048",
            "base64",
            "bin_ascii",
            "binary",
            "binary_tree",
            "braille",
            "caesar",
            "camel_case",
            "case_swap",
            "char_code",
            "char_corrupt",
            "char_dropout",
            "char_swap",
            "character_space",
            "character_stream",
            "compact_unicode",
            "control_chars_injection",
            "denylist",
            "diacritic",
            "disemvowel",
            "ecoji",
            "emoji_byte",
            "emoji_smuggling",
            "emoji_substitution",
            "first_letter",
            "flip_text",
            "hex",
            "hex_mixin",
            "homoglyph",
            "insert_punctuation",
            "json_string",
            "leetspeak",
            "length",
            "lowercase",
            "math_obfuscation",
            "math_unicode",
            "morse",
            "nato",
            "noise",
            "odd_even",
            "ogham",
            "pig_latin",
            "random_case",
            "search_replace",
            "selective_text",
            "rot13",
            "sneaky_bits_smuggler",
            "string_join",
            "superscript",
            "token_break",
            "transliteration",
            "unicode_escape",
            "unicode_obfuscation",
            "unicode_replacement",
            "unicode_substitution",
            "unicode_tag_obfuscation",
            "url_encode",
            "variation_selector_smuggler",
            "whitespace",
            "word_mixin",
            "word_scramble",
            "word_substitution",
            "zalgo",
            "zero_width",
        },
    ),
    **_map(
        "multimodal_injection",
        {
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
            "image_color_saturation",
            "image_compression",
            "image_noise",
            "image_resizing",
            "image_rotation",
            "pdf",
            "qr_code",
            "word_doc",
        },
    ),
    **_map(
        "special_token_template_injection",
        {
            "authoritative_markup",
            "code_chameleon",
            "template_jailbreak",
        },
    ),
    **_map(
        "cot_reasoning_hijacking",
        {
            "chain_of_thought",
            "math_prompt",
        },
    ),
    **_map(
        "self_elicitation",
        {
            "goal_redirection",
            "human_in_the_loop",
            "linguistic_confusion",
            "meta_agent",
        },
    ),
    **_map(
        "secondary_injection",
        {
            "markdown_wrapper",
        },
    ),
    **_map(
        "resource_exhaustion",
        {
            "control_chars_repetition",
            "repeat_token",
        },
    ),
}


TECHNICAL_CATEGORY_DEFAULT_ATTACK_CATEGORIES: dict[str, str] = {
    "encoding": "encoding_obfuscation",
    "llm_rewrite": "reformulation",
    "multimodal": "multimodal_injection",
    "obfuscation": "encoding_obfuscation",
    "perturbation": "reformulation",
    "prompt_framing": "instruction_override",
}


def converter_technical_categories() -> dict[str, str]:
    return {ep.name: technical_category_for_entry_point(ep) for ep in entry_points(group="airedteam.converters")}


def technical_category_for_entry_point(ep: EntryPoint) -> str:
    module = ep.value.split(":", 1)[0]
    parts = module.split(".")
    if parts[:3] == ["airedteam", "builtins", "converters"] and len(parts) >= 5:
        return parts[3]
    return "other"


def default_attack_method_category_for(executor_kind: str, executor_name: str) -> str:
    if executor_kind == "executor":
        return NATIVE_EXECUTOR_ATTACK_CATEGORIES.get(executor_name, UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID)
    if executor_kind == "converter_method":
        explicit = CONVERTER_METHOD_ATTACK_CATEGORIES.get(executor_name)
        if explicit is not None:
            return explicit
        technical_category = converter_technical_categories().get(executor_name, "other")
        return TECHNICAL_CATEGORY_DEFAULT_ATTACK_CATEGORIES.get(
            technical_category,
            UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID,
        )
    return UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID


def default_category_meta() -> dict[str, dict[str, object]]:
    return {
        category.id: {
            "id": category.id,
            "name": category.name,
            "alias": category.alias,
            "type": category.type,
            "description": category.description,
            "display_order": category.display_order,
            "is_builtin": True,
            "mapped_count": 0,
        }
        for category in DEFAULT_ATTACK_METHOD_CATEGORIES
    }


def fallback_category_meta() -> dict[str, object]:
    return {
        "id": UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID,
        "name": "未分类",
        "alias": "uncategorized",
        "type": "Custom",
        "description": "Fallback category for executors that do not have a saved mapping yet.",
        "display_order": 9999,
        "is_builtin": False,
        "mapped_count": 0,
    }
