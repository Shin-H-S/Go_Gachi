"""DB 테이블 모델 (SQLAlchemy ORM)."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base


class Folder(Base):
    """사용자가 생성한 광고 이미지 정리용 폴더."""

    __tablename__ = "folders"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_folders_user_id_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


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
    # 이 생성을 요청한 로그인 사용자의 Supabase UUID(JWT sub). 비로그인/익명이면 None.
    # "내 작업 기록" 조회·유저별 통계를 위한 소유권 표시이며, 캐시 키에는 포함하지 않는다.
    user_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    folder_id: Mapped[int | None] = mapped_column(
        ForeignKey("folders.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("generations.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    # 업로드 사진 바이트의 SHA256. 캐시 키의 핵심.
    image_hash: Mapped[str] = mapped_column(String(64), index=True)
    # develop의 프리셋 ID (예: "instagram_feed_square"). 이전 placement 칼럼을 대체.
    preset_id: Mapped[str] = mapped_column(String(80), index=True)
    # 사용자 요청(userPrompt) 정규화 후 SHA256. 같은 사진이라도 요청이 다르면 캐시 분리.
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


class Profile(Base):
    """로그인 사용자 1명의 앱 권한 정보 (Supabase auth.users와 별도로 우리가 관리).

    id에는 Supabase 로그인 토큰(JWT)의 ``sub`` 값(유저 UUID)을 문자열로 저장한다.
    auth.users에 하드 FK를 걸지 않아 스키마는 Alembic 한 곳에서 일관되게 관리한다.
    프로필 행은 첫 로그인 시 백엔드가 자동으로 만든다(없으면 role='user').
    """

    __tablename__ = "profiles"
    __table_args__ = (
        # role은 'user'/'admin'만 허용. 오타·임의 값으로 권한 체계가 조용히 깨지는 것을 DB가 막는다.
        CheckConstraint("role IN ('user', 'admin')", name="ck_profiles_role"),
    )

    # Supabase 유저 UUID(JWT sub). 우리 테이블의 기본키로 그대로 사용한다.
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # 'user' 또는 'admin'. 기본은 'user'이고 관리자 승격은 값만 바꾸면 된다.
    role: Mapped[str] = mapped_column(String(20), default="user", server_default="user", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
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
