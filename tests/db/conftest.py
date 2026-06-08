import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.database import Base


@pytest.fixture()
async def db_session() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_local = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_local() as db:
        yield db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
def tmp_dir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as name:
        yield Path(name)
