"""비동기 DB 연결·세션 인프라."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.app.core.config import get_settings


class Base(DeclarativeBase):
    """모든 ORM 모델의 베이스. 메타데이터를 모아 init_db가 한 번에 테이블을 만든다."""


def _async_database_url(database_url: str) -> str:
    """동기 DB URL이 들어와도 SQLAlchemy async 드라이버 URL로 보정한다."""
    if database_url.startswith("sqlite+aiosqlite"):
        return database_url
    if database_url.startswith("sqlite"):
        return database_url.replace("sqlite", "sqlite+aiosqlite", 1)
    if database_url.startswith("postgresql+asyncpg"):
        return database_url
    if database_url.startswith("postgresql"):
        return database_url.replace("postgresql", "postgresql+asyncpg", 1)
    return database_url


def _connect_args(database_url: str) -> dict[str, object]:
    """DB 종류별 연결 옵션."""
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


# 엔진은 앱 전체에서 1개만 재사용. pool_pre_ping=True로 죽은 연결을 자동 폐기한다.
_settings = get_settings()
ASYNC_DATABASE_URL = _async_database_url(_settings.database_url)
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    connect_args=_connect_args(ASYNC_DATABASE_URL),
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def async_init_db() -> None:
    """등록된 모든 테이블을 생성한다(이미 있으면 건너뜀). 앱 시작 시 한 번 호출."""
    # 모델 import를 함수 안에서: database를 import할 때 models를 끌고 오면 순환참조 위험.
    from backend.app.db import models  # noqa: F401

    # SQLite의 경우 DB 파일이 들어갈 폴더가 없으면 만들어둔다.
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def async_session_scope() -> AsyncIterator[AsyncSession]:
    """`async with` 블록 단위로 commit/rollback/close를 자동 처리한다.

    예외 발생 시 rollback 후 그대로 재발생한다.
    """
    db = AsyncSessionLocal()
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()
