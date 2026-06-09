import pytest

from airedteam.services.attack_method_categories import AttackMethodCategoryService
from airedteam.storage import models
from airedteam.storage.db import make_engine, make_sessionmaker


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
