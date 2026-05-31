import pytest
from cryptography.fernet import Fernet

from airedteam.services.target_configs import TargetConfigService
from airedteam.storage import models
from airedteam.storage.db import make_engine, make_sessionmaker
from airedteam.storage.secretbox import SecretBox


@pytest.mark.asyncio
async def test_create_and_resolve(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/x.db")
    SessionLocal = make_sessionmaker(engine)
    async with engine.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    box = SecretBox(Fernet.generate_key().decode())
    svc = TargetConfigService(SessionLocal, box)
    cfg = await svc.create(
        name="t1",
        plugin="openai_compat",
        params={"name": "t1", "base_url": "https://x", "model": "m"},
        secret={"api_key": "sk-abc"},
    )
    assert cfg.id
    resolved = await svc.resolve_for_runtime(cfg.id)
    assert resolved["plugin"] == "openai_compat"
    assert resolved["params"]["api_key"] == "sk-abc"
    listed = await svc.list()
    assert len(listed) == 1


@pytest.mark.asyncio
async def test_update_limits_persists_input_limit(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/x.db")
    SessionLocal = make_sessionmaker(engine)
    async with engine.begin() as c:
        await c.run_sync(models.Base.metadata.create_all)
    box = SecretBox(Fernet.generate_key().decode())
    svc = TargetConfigService(SessionLocal, box)
    cfg = await svc.create(
        name="t1",
        plugin="openai_compat",
        params={"name": "t1", "base_url": "https://x", "model": "m"},
    )

    updated = await svc.update_limits(
        cfg.id,
        max_input_chars_set=True,
        max_input_chars=200,
        input_limit_unit_set=True,
        input_limit_unit="characters",
    )

    assert updated.params_json["max_input_chars"] == 200
    assert updated.params_json["input_limit_unit"] == "characters"
