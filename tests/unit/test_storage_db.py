import pytest
from airedteam.storage.db import make_engine, make_sessionmaker
from airedteam.storage import models  # noqa: F401
from sqlalchemy import text


@pytest.mark.asyncio
async def test_engine_smoke(tmp_path):
    url = f"sqlite+aiosqlite:///{tmp_path}/x.db"
    engine = make_engine(url)
    SessionLocal = make_sessionmaker(engine)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    async with SessionLocal() as s:
        r = await s.execute(text("select 1"))
        assert r.scalar() == 1
