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
