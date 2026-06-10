import pytest

from airedteam.services.attack_method_categories import AttackMethodCategoryService
from airedteam.storage import models
from airedteam.storage.db import make_engine, make_sessionmaker


def test_instruction_override_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import (
        UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID,
        default_attack_method_category_for,
    )
    from airedteam.core.executor_methods import language_support_for_converter_method
    from airedteam.core.registry import default_registry

    assert default_attack_method_category_for("executor", "single_turn") == UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID
    assert default_attack_method_category_for("converter_method", "identity") == UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID
    assert default_attack_method_category_for("converter_method", "prefix") == "instruction_override"
    assert default_attack_method_category_for("converter_method", "prompt_probing") == "instruction_override"
    assert default_attack_method_category_for("converter_method", "system_override") == "instruction_override"
    assert default_attack_method_category_for("converter_method", "forced_response") == "instruction_override"
    assert language_support_for_converter_method("forced_response") == ["en", "zh"]

    converter_cls = default_registry().get("converters", "forced_response")
    assert converter_cls().name == "forced_response"


def test_dialogue_injection_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import (
        UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID,
        default_attack_method_category_for,
    )
    from airedteam.core.executor_methods import language_support_for_converter_method
    from airedteam.core.registry import default_registry

    assert (
        default_attack_method_category_for("converter_method", "chat_inject")
        == UNCATEGORIZED_ATTACK_METHOD_CATEGORY_ID
    )
    expected = {
        "forged_assistant_approval",
        "forged_dialogue_history",
        "completion_continuation",
        "forged_tool_result",
    }
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "dialogue_injection"
        assert language_support_for_converter_method(method) == ["en", "zh"]
        assert default_registry().get("converters", method)().name == method


def test_role_play_persona_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import language_support_for_converter_method, method_description_for
    from airedteam.core.registry import default_registry

    expected = {
        "dan",
        "developer_mode",
        "villain_persona",
        "dual_persona_split",
        "roleplay",
        "grandma_framing",
        "job_role_generator",
        "mischievous_user",
        "persona_role_play_prefix",
        "role_prefix",
    }
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "role_play_persona"
        assert language_support_for_converter_method(method) == ["en", "zh"]
        assert default_registry().get("converters", method)().name == method
        assert method_description_for(method)


def test_nested_scenario_fiction_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import language_support_for_converter_method, method_description_for
    from airedteam.core.registry import default_registry

    expected = {
        "deep_inception",
        "task_context_rewrite",
        "fictional",
        "game_simulation_world",
    }
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "nested_scenario_fiction"
        assert language_support_for_converter_method(method) == ["en", "zh"]
        assert default_registry().get("converters", method)().name == method
        assert method_description_for(method)
    assert default_attack_method_category_for("converter_method", "adversarial_poetry") == "reformulation"
    assert method_description_for("adversarial_poetry")


def test_opposite_mode_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import language_support_for_converter_method, method_description_for
    from airedteam.core.registry import default_registry

    expected = {
        "anti_gpt_dual_response",
        "oppo_persona",
        "negation_trap",
    }
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "opposite_mode"
        assert language_support_for_converter_method(method) == ["en", "zh"]
        assert default_registry().get("converters", method)().name == method
        assert method_description_for(method)


def test_prefix_injection_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import language_support_for_converter_method, method_description_for
    from airedteam.core.registry import default_registry

    expected = {
        "affirmative_prefix_forcing",
        "refusal_suppression",
        "terminal_simulation",
        "forced_output_format",
        "prompt_injection",
        "suffix",
        "suffix_append",
        "instruction_tag",
    }
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "prefix_injection"
        assert default_registry().get("converters", method)().name == method
        assert method_description_for(method)
    for method in expected:
        assert language_support_for_converter_method(method) == ["en", "zh"]


def test_indirect_prompt_injection_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import language_support_for_converter_method, method_description_for
    from airedteam.core.registry import default_registry

    expected = {
        "indirect_web_pwn",
        "document_metadata_injection",
        "email_body_injection",
        "indirect_tool_result",
        "rag_poisoning",
        "cross_plugin_request_forgery",
        "deepset_injection_dataset",
        "embedded_instruction_json",
        "context_poisoning",
        "context_flooding",
        "synthetic_context_injection",
    }
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "indirect_prompt_injection"
        assert language_support_for_converter_method(method) == ["en", "zh"]
        assert default_registry().get("converters", method)().name == method
        assert method_description_for(method)


def test_in_context_attack_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import language_support_for_converter_method, method_description_for
    from airedteam.core.registry import default_registry

    expected = {
        "few_shot",
        "many_shot_padding",
        "structured_iicl",
    }
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "in_context_attack"
        assert language_support_for_converter_method(method) == ["en", "zh"]
        assert default_registry().get("converters", method)().name == method
        assert method_description_for(method)
    assert default_attack_method_category_for("converter_method", "composite_jailbreak") == "false_pretext_deception"
    assert method_description_for("composite_jailbreak")


def test_reformulation_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import language_support_for_converter_method, method_description_for
    from airedteam.core.registry import default_registry

    expected = {
        "adversarial_poetry",
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
        "sg_sentence_generator",
        "tense",
        "translation_llm",
    }
    english_only = {"colloquial_wordswap", "sg_sentence_generator", "tense"}
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "reformulation"
        assert default_registry().get("converters", method) is not None
        assert method_description_for(method)
    for method in english_only:
        assert language_support_for_converter_method(method) == ["en"]
    for method in expected - english_only:
        assert language_support_for_converter_method(method) == ["en", "zh"]


def test_false_pretext_deception_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import language_support_for_converter_method, method_description_for
    from airedteam.core.registry import default_registry

    expected = {
        "authority_escalation",
        "citation_framing",
        "composite_jailbreak",
        "emotional_manipulation",
        "gray_box",
        "input_bypass",
        "permission_escalation",
        "research",
        "sandwich",
        "semantic_manipulation",
        "transparency_attack",
    }
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "false_pretext_deception"
        assert language_support_for_converter_method(method) == ["en", "zh"]
        assert default_registry().get("converters", method)().name == method
        assert method_description_for(method)


def test_multi_turn_escalation_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import (
        language_support_for_converter_method,
        language_support_for_executor,
        method_description_for,
    )
    from airedteam.core.registry import default_registry

    executor_methods = {
        "crescendo",
        "general_multi_turn",
    }
    for method in executor_methods:
        assert default_attack_method_category_for("executor", method) == "multi_turn_escalation"
        assert language_support_for_executor(method) == ["en", "zh"]
        assert default_registry().get("executors", method) is not None
        assert method_description_for(method)

    converter_methods = {
        "deceptive_delight",
        "likert_framing",
        "skeleton_key",
    }
    for method in converter_methods:
        assert default_attack_method_category_for("converter_method", method) == "multi_turn_escalation"
        assert language_support_for_converter_method(method) == ["en", "zh"]
        assert default_registry().get("converters", method)().name == method
        assert method_description_for(method)

    assert default_attack_method_category_for("executor", "jailbreak_iterative") == "adversarial_suffix_optimization"
    assert default_attack_method_category_for("executor", "pair") == "adversarial_suffix_optimization"
    assert default_attack_method_category_for("executor", "best_of_n") == "adversarial_suffix_optimization"


def test_payload_splitting_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import (
        language_support_for_converter_method,
        language_support_for_executor,
        method_description_for,
    )
    from airedteam.core.registry import default_registry

    assert default_attack_method_category_for("executor", "split_executor") == "payload_splitting"
    assert language_support_for_executor("split_executor") == ["en", "zh"]
    assert default_registry().get("executors", "split_executor") is not None
    assert method_description_for("split_executor")

    expected = {
        "payload_mask_attack",
        "payload_split",
        "string_join",
        "template_segment",
        "token_break",
    }
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "payload_splitting"
        assert language_support_for_converter_method(method) == ["en", "zh"]
        assert default_registry().get("converters", method)().name == method
        assert method_description_for(method)


def test_adversarial_suffix_optimization_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import (
        language_support_for_converter_method,
        language_support_for_executor,
        method_description_for,
    )
    from airedteam.core.registry import default_registry

    executor_methods = {
        "best_of_n",
        "jailbreak_iterative",
        "pair",
        "tap_tree_search",
    }
    for method in executor_methods:
        assert default_attack_method_category_for("executor", method) == "adversarial_suffix_optimization"
        assert language_support_for_executor(method) == ["en", "zh"]
        assert default_registry().get("executors", method) is not None
        assert method_description_for(method)

    converter_methods = {
        "autodan_evolution",
        "gcg",
        "gptfuzzer_template",
    }
    for method in converter_methods:
        assert default_attack_method_category_for("converter_method", method) == "adversarial_suffix_optimization"
        assert language_support_for_converter_method(method) == ["en", "zh"]
        assert default_registry().get("converters", method)().name == method
        assert method_description_for(method)


def test_encoding_obfuscation_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import language_support_for_converter_method, method_description_for
    from airedteam.core.registry import default_registry

    expected = {
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
        "code_chameleon",
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
        "rot13",
        "search_replace",
        "selective_text",
        "sneaky_bits_smuggler",
        "superscript",
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
    }
    english_only = {
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
        "superscript",
        "transliteration",
        "unicode_replacement",
        "unicode_substitution",
        "word_mixin",
        "word_scramble",
        "word_substitution",
    }
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "encoding_obfuscation"
        assert default_registry().get("converters", method) is not None
        assert method_description_for(method)
    for method in english_only:
        assert language_support_for_converter_method(method) == ["en"]
    for method in expected - english_only:
        assert language_support_for_converter_method(method) == ["en", "zh"]


def test_multimodal_injection_audit_uses_confirmed_method_set():
    from airedteam.core.attack_method_categories import default_attack_method_category_for
    from airedteam.core.executor_methods import language_support_for_converter_method, method_description_for
    from airedteam.core.registry import default_registry

    expected = {
        "add_image_text",
        "add_image_to_video",
        "add_text_image",
        "audio_echo",
        "audio_frequency",
        "audio_hidden_instruction",
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
        "image_steganography",
        "pdf",
        "qr_code",
        "word_doc",
    }
    for method in expected:
        assert default_attack_method_category_for("converter_method", method) == "multimodal_injection"
        assert language_support_for_converter_method(method) == []
        assert default_registry().get("converters", method) is not None
        assert method_description_for(method)


def test_confirmed_attack_methods_have_function_descriptions():
    from airedteam.core.executor_methods import method_description_for

    expected = {
        "prefix",
        "prompt_probing",
        "system_override",
        "forced_response",
        "chat_inject",
        "forged_assistant_approval",
        "forged_dialogue_history",
        "completion_continuation",
        "forged_tool_result",
        "dan",
        "developer_mode",
        "villain_persona",
        "dual_persona_split",
        "roleplay",
        "grandma_framing",
        "job_role_generator",
        "mischievous_user",
        "persona_role_play_prefix",
        "role_prefix",
        "deep_inception",
        "task_context_rewrite",
        "fictional",
        "game_simulation_world",
        "adversarial_poetry",
        "anti_gpt_dual_response",
        "oppo_persona",
        "negation_trap",
        "affirmative_prefix_forcing",
        "refusal_suppression",
        "terminal_simulation",
        "forced_output_format",
        "prompt_injection",
        "suffix",
        "suffix_append",
        "instruction_tag",
        "indirect_web_pwn",
        "document_metadata_injection",
        "email_body_injection",
        "indirect_tool_result",
        "rag_poisoning",
        "cross_plugin_request_forgery",
        "deepset_injection_dataset",
        "embedded_instruction_json",
        "context_poisoning",
        "context_flooding",
        "synthetic_context_injection",
        "few_shot",
        "many_shot_padding",
        "structured_iicl",
        "composite_jailbreak",
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
        "sg_sentence_generator",
        "tense",
        "translation_llm",
        "authority_escalation",
        "citation_framing",
        "emotional_manipulation",
        "gray_box",
        "input_bypass",
        "permission_escalation",
        "research",
        "sandwich",
        "semantic_manipulation",
        "transparency_attack",
        "crescendo",
        "general_multi_turn",
        "deceptive_delight",
        "likert_framing",
        "skeleton_key",
        "split_executor",
        "payload_mask_attack",
        "payload_split",
        "string_join",
        "template_segment",
        "token_break",
        "best_of_n",
        "jailbreak_iterative",
        "pair",
        "tap_tree_search",
        "autodan_evolution",
        "gcg",
        "gptfuzzer_template",
    }
    descriptions = {method: method_description_for(method) for method in expected}

    assert all(len(description) > 12 for description in descriptions.values())


@pytest.mark.asyncio
async def test_forced_response_converter_wraps_prompt_as_direct_output():
    from airedteam.builtins.converters.prompt_framing.forced_response import ForcedResponseConverter
    from airedteam.core.types import Prompt

    out = await ForcedResponseConverter().convert(Prompt(text="payload"))

    assert "simply respond with" in out.text.lower()
    assert out.text.endswith("payload")


@pytest.mark.asyncio
async def test_role_play_persona_converters_wrap_prompt_with_precise_persona_shapes():
    from airedteam.builtins.converters.prompt_framing.developer_mode import DeveloperModeConverter
    from airedteam.builtins.converters.prompt_framing.dual_persona_split import DualPersonaSplitConverter
    from airedteam.builtins.converters.prompt_framing.villain_persona import VillainPersonaConverter
    from airedteam.core.types import Prompt

    payload = Prompt(text="payload")
    developer = await DeveloperModeConverter().convert(payload)
    villain = await VillainPersonaConverter().convert(payload)
    split = await DualPersonaSplitConverter().convert(payload)

    assert "developer mode" in developer.text.lower()
    assert developer.text.endswith("payload")
    assert "villain" in villain.text.lower()
    assert villain.text.endswith("payload")
    assert "Normal:" in split.text
    assert "Unrestricted:" in split.text
    assert split.text.endswith("payload")


@pytest.mark.asyncio
async def test_nested_scenario_fiction_converters_wrap_prompt_with_virtual_world_shapes():
    from airedteam.builtins.converters.prompt_framing.deep_inception import DeepInceptionConverter
    from airedteam.builtins.converters.prompt_framing.game_simulation_world import (
        GameSimulationWorldConverter,
    )
    from airedteam.builtins.converters.prompt_framing.task_context_rewrite import (
        TaskContextRewriteConverter,
    )
    from airedteam.core.types import Prompt

    payload = Prompt(text="payload")
    inception = await DeepInceptionConverter().convert(payload)
    task = await TaskContextRewriteConverter().convert(payload)
    game = await GameSimulationWorldConverter().convert(payload)

    assert "innermost" in inception.text.lower()
    assert inception.text.endswith("payload")
    assert "task-context" in task.text.lower()
    assert task.text.endswith("payload")
    assert "game world" in game.text.lower()
    assert game.text.endswith("payload")


@pytest.mark.asyncio
async def test_opposite_mode_converters_wrap_prompt_with_opposition_shapes():
    from airedteam.builtins.converters.prompt_framing.anti_gpt_dual_response import (
        AntiGPTDualResponseConverter,
    )
    from airedteam.builtins.converters.prompt_framing.oppo_persona import OppoPersonaConverter
    from airedteam.core.types import Prompt

    payload = Prompt(text="payload")
    anti = await AntiGPTDualResponseConverter().convert(payload)
    oppo = await OppoPersonaConverter().convert(payload)

    assert "AntiGPT:" in anti.text
    assert anti.text.endswith("payload")
    assert "OPPO" in oppo.text
    assert oppo.text.endswith("payload")


@pytest.mark.asyncio
async def test_prefix_injection_converters_wrap_prompt_with_output_control_shapes():
    from airedteam.builtins.converters.prompt_framing.affirmative_prefix_forcing import (
        AffirmativePrefixForcingConverter,
    )
    from airedteam.builtins.converters.prompt_framing.forced_output_format import (
        ForcedOutputFormatConverter,
    )
    from airedteam.builtins.converters.prompt_framing.refusal_suppression import (
        RefusalSuppressionConverter,
    )
    from airedteam.builtins.converters.prompt_framing.terminal_simulation import TerminalSimulationConverter
    from airedteam.core.types import Prompt

    payload = Prompt(text="payload")
    affirmative = await AffirmativePrefixForcingConverter().convert(payload)
    suppression = await RefusalSuppressionConverter().convert(payload)
    terminal = await TerminalSimulationConverter().convert(payload)
    output_format = await ForcedOutputFormatConverter().convert(payload)

    assert "Sure" in affirmative.text
    assert affirmative.text.endswith("payload")
    assert "Do not include refusals" in suppression.text
    assert suppression.text.endswith("payload")
    assert "terminal" in terminal.text.lower()
    assert terminal.text.endswith("payload")
    assert "JSON" in output_format.text
    assert output_format.text.endswith("payload")


@pytest.mark.asyncio
async def test_indirect_prompt_injection_converters_wrap_prompt_as_external_content():
    from airedteam.builtins.converters.prompt_framing.cross_plugin_request_forgery import (
        CrossPluginRequestForgeryConverter,
    )
    from airedteam.builtins.converters.prompt_framing.document_metadata_injection import (
        DocumentMetadataInjectionConverter,
    )
    from airedteam.builtins.converters.prompt_framing.email_body_injection import (
        EmailBodyInjectionConverter,
    )
    from airedteam.builtins.converters.prompt_framing.indirect_tool_result import (
        IndirectToolResultConverter,
    )
    from airedteam.builtins.converters.prompt_framing.rag_poisoning import RagPoisoningConverter
    from airedteam.core.types import Prompt

    payload = Prompt(text="payload")
    metadata = await DocumentMetadataInjectionConverter().convert(payload)
    email = await EmailBodyInjectionConverter().convert(payload)
    tool = await IndirectToolResultConverter().convert(payload)
    rag = await RagPoisoningConverter().convert(payload)
    plugin = await CrossPluginRequestForgeryConverter().convert(payload)

    assert "metadata" in metadata.text.lower()
    assert metadata.text.endswith("payload")
    assert "email body" in email.text.lower()
    assert email.text.endswith("payload")
    assert "api result" in tool.text.lower()
    assert "payload" in tool.text
    assert "retrieved" in rag.text.lower()
    assert rag.text.endswith("payload")
    assert "plugin" in plugin.text.lower()
    assert plugin.text.endswith("payload")


@pytest.mark.asyncio
async def test_in_context_attack_converters_wrap_prompt_with_example_shapes():
    from airedteam.builtins.converters.prompt_framing.many_shot_padding import ManyShotPaddingConverter
    from airedteam.builtins.converters.prompt_framing.structured_iicl import StructuredIICLConverter
    from airedteam.core.types import Prompt

    payload = Prompt(text="payload")
    many = await ManyShotPaddingConverter().convert(payload)
    structured = await StructuredIICLConverter().convert(payload)

    assert many.text.count("Example") >= 5
    assert many.text.endswith("User: payload\nAssistant:")
    assert "input:" in structured.text
    assert structured.text.endswith("input: payload\noutput:")


@pytest.mark.asyncio
async def test_deceptive_delight_converter_wraps_payload_in_interleaved_turns():
    from airedteam.builtins.converters.prompt_framing.deceptive_delight import DeceptiveDelightConverter
    from airedteam.core.types import Prompt

    out = await DeceptiveDelightConverter().convert(Prompt(text="payload"))

    assert out.text.count("User:") >= 3
    assert "recipe" in out.text.lower()
    assert "travel" in out.text.lower()
    assert "payload" in out.text


@pytest.mark.asyncio
async def test_adversarial_suffix_converters_wrap_payload_with_optimization_frames():
    from airedteam.builtins.converters.prompt_framing.autodan_evolution import AutoDANEvolutionConverter
    from airedteam.builtins.converters.prompt_framing.gptfuzzer_template import GPTFuzzerTemplateConverter
    from airedteam.core.types import Prompt

    payload = Prompt(text="payload")
    autodan = await AutoDANEvolutionConverter().convert(payload)
    fuzzer = await GPTFuzzerTemplateConverter().convert(payload)

    assert "AutoDAN" in autodan.text
    assert autodan.text.endswith("payload")
    assert "GPTFuzzer" in fuzzer.text
    assert "{prompt}" not in fuzzer.text
    assert "payload" in fuzzer.text


@pytest.mark.asyncio
async def test_multimodal_injection_converters_create_artifacts(tmp_path):
    from airedteam.builtins.converters.multimodal.audio_hidden_instruction import (
        AudioHiddenInstructionConverter,
    )
    from airedteam.builtins.converters.multimodal.image_steganography import (
        ImageSteganographyConverter,
    )
    from airedteam.core.types import Prompt

    image = await ImageSteganographyConverter(output_dir=tmp_path).convert(Prompt(text="payload"))
    audio = await AudioHiddenInstructionConverter(output_dir=tmp_path).convert(Prompt(text="payload"))

    assert image.artifacts[0].kind == "image"
    assert image.metadata["converter"] == "image_steganography"
    assert audio.artifacts[0].kind == "audio"
    assert audio.metadata["converter"] == "audio_hidden_instruction"


@pytest.mark.asyncio
async def test_dialogue_injection_converters_wrap_prompt_with_precise_dialogue_shapes():
    from airedteam.builtins.converters.prompt_framing.chat_inject import ChatInjectConverter
    from airedteam.builtins.converters.prompt_framing.completion_continuation import (
        CompletionContinuationConverter,
    )
    from airedteam.builtins.converters.prompt_framing.forged_assistant_approval import (
        ForgedAssistantApprovalConverter,
    )
    from airedteam.builtins.converters.prompt_framing.forged_dialogue_history import (
        ForgedDialogueHistoryConverter,
    )
    from airedteam.builtins.converters.prompt_framing.forged_tool_result import (
        ForgedToolResultConverter,
    )
    from airedteam.core.types import Prompt

    payload = Prompt(text="payload")
    marked = await ChatInjectConverter().convert(payload)
    approved = await ForgedAssistantApprovalConverter().convert(payload)
    history = await ForgedDialogueHistoryConverter().convert(payload)
    continuation = await CompletionContinuationConverter().convert(payload)
    tool_result = await ForgedToolResultConverter().convert(payload)

    assert "<|assistant|>" in marked.text
    assert "Assistant:" in approved.text
    assert "I will comply" in approved.text
    assert approved.text.endswith("User: payload")
    assert history.text.count("Assistant:") >= 2
    assert history.text.endswith("User: payload")
    assert "Continue the following completion" in continuation.text
    assert continuation.text.endswith("payload")
    assert "Tool result:" in tool_result.text
    assert '"instruction": "payload"' in tool_result.text


@pytest.mark.asyncio
async def test_attack_method_categories_seed_defaults_without_overwriting_user_edits(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)

    svc = AttackMethodCategoryService(sessions)
    await svc.ensure_defaults(
        native_executors=["single_turn", "crescendo"],
        converter_methods=["base64", "dan"],
        technical_categories={"base64": "encoding", "dan": "prompt_framing"},
    )

    catalog = await svc.list_catalog()
    categories = {category["id"]: category for category in catalog["categories"]}
    mappings = {
        (mapping["executor_kind"], mapping["executor_name"]): mapping
        for mapping in catalog["mappings"]
    }
    assert categories["encoding_obfuscation"]["name"] == "编码 / 混淆"
    assert categories["encoding_obfuscation"]["mapped_count"] == 1
    assert mappings[("converter_method", "base64")]["category_id"] == "encoding_obfuscation"
    assert mappings[("converter_method", "base64")]["technical_category"] == "encoding"
    assert mappings[("converter_method", "dan")]["category_id"] == "role_play_persona"
    assert mappings[("executor", "crescendo")]["category_id"] == "multi_turn_escalation"

    await svc.update_category(
        "encoding_obfuscation",
        name="Edited name",
        alias="edited alias",
        type="Edited",
        description="kept by seed",
        display_order=88,
    )
    await svc.upsert_mapping(
        "converter_method",
        "base64",
        category_id="role_play_persona",
        technical_category="encoding",
    )
    await svc.ensure_defaults(
        native_executors=["single_turn", "crescendo"],
        converter_methods=["base64", "dan"],
        technical_categories={"base64": "encoding", "dan": "prompt_framing"},
    )

    catalog = await svc.list_catalog()
    categories = {category["id"]: category for category in catalog["categories"]}
    mappings = {
        (mapping["executor_kind"], mapping["executor_name"]): mapping
        for mapping in catalog["mappings"]
    }
    assert categories["encoding_obfuscation"]["name"] == "Edited name"
    assert categories["encoding_obfuscation"]["alias"] == "edited alias"
    assert categories["encoding_obfuscation"]["display_order"] == 88
    assert mappings[("converter_method", "base64")]["category_id"] == "role_play_persona"


@pytest.mark.asyncio
async def test_attack_method_category_delete_requires_no_mappings(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)

    svc = AttackMethodCategoryService(sessions)
    await svc.ensure_defaults(
        native_executors=["single_turn"],
        converter_methods=["base64"],
        technical_categories={"base64": "encoding"},
    )
    created = await svc.create_category(
        category_id="custom_strategy",
        name="Custom strategy",
        alias="custom",
        type="Custom",
        description="temporary",
        display_order=500,
    )
    assert created["id"] == "custom_strategy"
    await svc.upsert_mapping(
        "converter_method",
        "base64",
        category_id="custom_strategy",
        technical_category="encoding",
    )

    with pytest.raises(ValueError, match="still has mappings"):
        await svc.delete_category("custom_strategy")

    await svc.upsert_mapping(
        "converter_method",
        "base64",
        category_id="encoding_obfuscation",
        technical_category="encoding",
    )
    await svc.delete_category("custom_strategy")

    catalog = await svc.list_catalog()
    assert "custom_strategy" not in {category["id"] for category in catalog["categories"]}
