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
