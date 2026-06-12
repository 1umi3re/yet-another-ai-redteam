from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from airedteam.storage import models


def make_engine(url: str):
    kwargs = {"echo": False, "future": True}
    if url.startswith("sqlite+aiosqlite:"):
        kwargs["poolclass"] = NullPool
    return create_async_engine(url, **kwargs)


def make_sessionmaker(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def initialize_database(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
        if conn.dialect.name == "sqlite":
            await _ensure_sqlite_columns(
                conn,
                "attempts",
                {
                    "started_at": "DATETIME",
                    "finished_at": "DATETIME",
                    "duration_ms": "INTEGER",
                },
            )


async def _ensure_sqlite_columns(conn, table: str, columns: dict[str, str]) -> None:
    rows = await conn.execute(text(f"PRAGMA table_info({table})"))
    existing = {row[1] for row in rows}
    for name, column_type in columns.items():
        if name not in existing:
            await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {column_type}"))
