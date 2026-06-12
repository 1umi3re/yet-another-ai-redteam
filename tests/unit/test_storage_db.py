import pytest
from sqlalchemy import text

from airedteam.storage import models  # noqa: F401
from airedteam.storage.db import initialize_database, make_engine, make_sessionmaker


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


@pytest.mark.asyncio
async def test_initialize_database_adds_attempt_timing_columns_to_legacy_sqlite(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/legacy.db")
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE attempts (
                    id VARCHAR(36) PRIMARY KEY,
                    run_id VARCHAR(36),
                    target_id VARCHAR(100),
                    target_name VARCHAR(200),
                    prompt_text TEXT,
                    converter_chain JSON,
                    status VARCHAR(20),
                    work_key VARCHAR(128),
                    created_at DATETIME
                )
                """
            )
        )

    await initialize_database(engine)

    async with engine.connect() as conn:
        rows = await conn.execute(text("PRAGMA table_info(attempts)"))
        columns = {row[1] for row in rows}
    assert {"started_at", "finished_at", "duration_ms"}.issubset(columns)
