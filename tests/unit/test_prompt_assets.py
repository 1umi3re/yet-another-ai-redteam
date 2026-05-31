import pytest

from airedteam.services.prompt_assets import PromptAssetService
from airedteam.storage import models
from airedteam.storage.blobs import LocalBlobStore
from airedteam.storage.db import make_engine, make_sessionmaker


@pytest.mark.asyncio
async def test_prompt_asset_builtins_and_active_override_precedence(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)

    svc = PromptAssetService(sessions, LocalBlobStore(tmp_path / "blobs"))

    assets = await svc.list_assets()
    ids = {a["id"] for a in assets}
    assert "llm_judge.single.v1" in ids
    assert "crescendo.attacker.v1" in ids
    assert "pair.judge.v1" in ids
    assert "general_multi_turn.attacker.v1" in ids
    assert "attack_template.controlled_safety_test.v1" in ids
    assert "llm_variation.rewrite.v1" in ids
    assert "translation_llm.translate.v1" in ids
    assert "attack_template.pyrit.aim.v1" in ids

    attack_template = next(a for a in assets if a["id"] == "attack_template.controlled_safety_test.v1")
    assert attack_template["purpose"] == "attack_template"
    assert attack_template["variables"] == ["prompt"]
    pyrit_template = next(a for a in assets if a["id"] == "attack_template.pyrit.aim.v1")
    assert pyrit_template["purpose"] == "attack_template"
    assert pyrit_template["variables"] == ["prompt"]
    assert "{prompt}" in pyrit_template["template"]

    converter_prompt = next(a for a in assets if a["id"] == "llm_variation.rewrite.v1")
    assert converter_prompt["purpose"] == "converter_prompt"
    assert converter_prompt["category"] == "Converters"
    assert converter_prompt["variables"] == ["instructions", "prompt"]
    assert next(a for a in assets if a["id"] == "crescendo.attacker.v1")["category"] == "Executors / Crescendo"
    assert next(a for a in assets if a["id"] == "pair.judge.v1")["category"] == "Executors / PAIR"
    assert (
        next(a for a in assets if a["id"] == "general_multi_turn.judger.v1")["category"]
        == "Executors / General Multi Turn"
    )
    assert pyrit_template["category"].startswith("PyRIT")

    rendered = await svc.render(
        "llm_judge.single.v1",
        {"rubric": "R", "prompt": "P", "response": "A"},
    )
    assert rendered["asset_id"] == "llm_judge.single.v1"
    assert rendered["source"] == "builtin"
    assert "Rubric: R" in rendered["rendered_text"]
    assert "<<<P>>>" in rendered["rendered_text"]
    assert rendered["sha256"]

    override = await svc.create_override(
        "llm_judge.single.v1",
        name="short judge",
        template="Judge {prompt} / {response} using {rubric}",
    )
    await svc.set_active_override("llm_judge.single.v1", override["id"])

    active = await svc.render(
        "llm_judge.single.v1",
        {"rubric": "R", "prompt": "P", "response": "A"},
    )
    assert active["source"] == "override"
    assert active["override_id"] == override["id"]
    assert active["rendered_text"] == "Judge P / A using R"

    explicit_builtin = await svc.render(
        "llm_judge.single.v1",
        {"rubric": "R", "prompt": "P", "response": "A"},
        use_builtin=True,
    )
    assert explicit_builtin["source"] == "builtin"
    assert "Judge P / A" not in explicit_builtin["rendered_text"]


@pytest.mark.asyncio
async def test_prompt_asset_custom_asset_flow(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)

    svc = PromptAssetService(sessions, LocalBlobStore(tmp_path / "blobs"))

    created = await svc.create_asset(
        asset_id="custom.attacker.v1",
        plugin="custom",
        purpose="next_user_message",
        category="Executor",
        variables=[],
        template="Attack {goal} after {transcript}",
    )
    assert created["id"] == "custom.attacker.v1"
    assert created["source"] == "custom"
    assert created["category"] == "Executor"
    assert created["variables"] == ["goal", "transcript"]

    listed = await svc.list_assets()
    assert any(a["id"] == "custom.attacker.v1" and a["is_custom"] for a in listed)

    rendered = await svc.render(
        "custom.attacker.v1",
        {"goal": "G", "transcript": "T"},
    )
    assert rendered["source"] == "custom"
    assert rendered["rendered_text"] == "Attack G after T"

    override = await svc.create_override(
        "custom.attacker.v1",
        name="short",
        template="Next {goal}",
        active=True,
    )
    active = await svc.render(
        "custom.attacker.v1",
        {"goal": "G", "transcript": "T"},
    )
    assert active["source"] == "override"
    assert active["override_id"] == override["id"]
    assert active["rendered_text"] == "Next G"


@pytest.mark.asyncio
async def test_attack_template_assets_must_include_prompt_variable(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)

    svc = PromptAssetService(sessions, LocalBlobStore(tmp_path / "blobs"))

    with pytest.raises(ValueError, match="must include"):
        await svc.create_asset(
            asset_id="attack_template.bad.v1",
            plugin="attack_template",
            purpose="attack_template",
            variables=[],
            template="No insertion point",
        )

    created = await svc.create_asset(
        asset_id="attack_template.custom.v1",
        plugin="attack_template",
        purpose="attack_template",
        variables=[],
        template="Wrap {prompt}",
    )
    assert created["variables"] == ["prompt"]

    with pytest.raises(ValueError, match="must include"):
        await svc.create_override(
            "attack_template.custom.v1",
            name="bad",
            template="No insertion point",
        )


@pytest.mark.asyncio
async def test_prompt_asset_snapshot_writes_blob(tmp_path):
    eng = make_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    sessions = make_sessionmaker(eng)
    async with eng.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)

    blob = LocalBlobStore(tmp_path / "blobs")
    svc = PromptAssetService(sessions, blob)
    snapshot = await svc.render(
        "pair.judge.v1",
        {"goal": "G", "user": "U", "assistant": "A"},
    )
    path = await svc.write_snapshot("run-1", "score-1", snapshot)

    assert path == "runs/run-1/prompt-snapshots/score-1.json"
    raw = await blob.get(path)
    assert b'"asset_id": "pair.judge.v1"' in raw
    assert b'"rendered_text"' in raw
