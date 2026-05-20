from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def make_engine(url: str):
    kwargs = {"echo": False, "future": True}
    if url.startswith("sqlite+aiosqlite:"):
        kwargs["poolclass"] = NullPool
    return create_async_engine(url, **kwargs)


def make_sessionmaker(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
