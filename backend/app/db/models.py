"""DB 테이블 정의 (SQLAlchemy ORM).

베이스라인: sessions, generations.
(messages 테이블 = 수정요청 대화 기록용, 고도화 단계에서 추가)
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class WorkSession(Base):
    """작업 세션 — 한 번의 생성 작업 단위 (테이블명: sessions)."""

    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Generation(Base):
    """생성 결과 기록 (테이블명: generations)."""

    __tablename__ = "generations"

    generation_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("sessions.session_id")
    )
    original_image_path: Mapped[str] = mapped_column(String(500))
    generated_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ad_copy: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
