"""DB 테이블 모델 (SQLAlchemy ORM)."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base


class Generation(Base):
    """광고 생성 시도 1건(또는 캐시 히트 1건)을 표현하는 행.

    status 흐름: pending → success / failed / cached.
    캐시 조회용 복합 인덱스를 걸어 같은 입력 재요청 시 빠르게 찾는다.
    """

    __tablename__ = "generations"
    __table_args__ = (
        # 캐시 조회용 복합 인덱스. find_cached_generation의 WHERE 컬럼과 정확히 일치.
        Index(
            "ix_generations_cache_lookup",
            "image_hash",
            "preset_id",
            "instruction_hash",
            "model",
            "prompt_version",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 요청 1건을 식별하는 UUID. 라우터·로그·응답에서 모두 같은 값을 쓴다.
    request_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    # 업로드 사진 바이트의 SHA256. 캐시 키의 핵심.
    image_hash: Mapped[str] = mapped_column(String(64), index=True)
    # develop의 프리셋 ID (예: "instagram_feed_square"). 이전 placement 칼럼을 대체.
    preset_id: Mapped[str] = mapped_column(String(80), index=True)
    # 사용자 추가 지시문(feedback) 정규화 후 SHA256. 같은 사진이라도 지시가 다르면 캐시 분리.
    instruction_hash: Mapped[str] = mapped_column(String(64), index=True)
    prompt_version: Mapped[str] = mapped_column(String(80), index=True)
    model: Mapped[str] = mapped_column(String(120), index=True)
    # 원본/결과 이미지의 디스크 경로. 캐시 hit 검증 시 실제 파일 존재 여부도 확인.
    original_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    output_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # 프론트가 결과를 가져갈 정적 URL 또는 외부 저장소 URL (다음 주 GCS 이전 시 사용).
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    # pending / success / failed / cached 중 하나.
    status: Mapped[str] = mapped_column(String(30), index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # 상태 전이 시점 추적용. mark_*_success/failed가 호출될 때 자동 갱신.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ApiUsage(Base):
    """OpenAI 호출 1건의 비용·캐시 여부 기록 (내부 모니터링용)."""

    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 같은 request_id의 Generation 행과 짝지어진다.
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(50), default="openai")
    model: Mapped[str] = mapped_column(String(120), index=True)
    operation: Mapped[str] = mapped_column(String(80), default="image_edit")
    # 추정 비용(USD). 캐시 hit이면 0.0.
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    # 이번 호출이 캐시 hit이었나(True면 실제 OpenAI 호출 없음).
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
