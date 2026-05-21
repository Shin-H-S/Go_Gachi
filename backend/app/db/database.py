"""MySQL 연결 설정 (SQLAlchemy).

엔진/세션을 만들고, 테이블 생성과 요청별 세션 제공(get_db)을 담당한다.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core import config

# DB 엔진 (pool_pre_ping: 끊긴 커넥션 자동 감지)
engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, echo=False)

# 요청마다 새 세션을 찍어내는 공장
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """모든 ORM 모델이 상속하는 베이스 클래스."""


def init_db() -> None:
    """정의된 모든 테이블을 DB에 생성한다(이미 있으면 건너뜀).

    Args:
        없음.
    Returns:
        None.
    """
    from app.db import models  # noqa: F401  (import 해야 테이블이 Base에 등록됨)

    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    """요청마다 DB 세션을 열고, 끝나면 닫는다 (FastAPI 의존성).

    Args:
        없음.
    Yields:
        SQLAlchemy 세션 객체.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
