"""generations 테이블 CRUD. 상태 전이: pending → success/failed, 캐시 hit는 cached로 별도 행."""

import asyncio
import hashlib
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Generation

_WHITESPACE_RE = re.compile(r"\s+")


def image_sha256(file_bytes: bytes) -> str:
    """캐시 키로 쓸 이미지 해시."""
    return hashlib.sha256(file_bytes).hexdigest()


def normalize_instruction(user_prompt: str | None) -> str:
    """공백·줄바꿈을 한 칸으로 합쳐 캐시 키 비교를 안정시킨다."""
    if not user_prompt:
        return ""
    stripped = user_prompt.strip()
    return _WHITESPACE_RE.sub(" ", stripped) if stripped else ""


def instruction_sha256(user_prompt: str | None) -> str:
    """캐시 키 비교용 사용자 입력 해시."""
    normalized = normalize_instruction(user_prompt)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def find_cached_generation(
    db: AsyncSession,
    *,
    image_hash: str,
    preset_id: str,
    instruction_hash: str,
    model: str,
    prompt_version: str,
) -> Generation | None:
    """최신 success 행을 찾되, 결과 파일이 실제로 남아있는 행만 돌려준다(사라진 옛 기록은 스킵)."""
    stmt = (
        select(Generation)
        .where(Generation.image_hash == image_hash)
        .where(Generation.preset_id == preset_id)
        .where(Generation.instruction_hash == instruction_hash)
        .where(Generation.model == model)
        .where(Generation.prompt_version == prompt_version)
        .where(Generation.status == "success")
        .order_by(Generation.created_at.desc(), Generation.id.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def list_cached_generations(
    db: AsyncSession,
    *,
    image_hash: str,
    preset_id: str,
    instruction_hash: str,
    model: str,
    prompt_version: str,
) -> list[Generation]:
    """캐시 조건에 맞는 success 후보 행을 최신순으로 돌려준다."""
    stmt = (
        select(Generation)
        .where(Generation.image_hash == image_hash)
        .where(Generation.preset_id == preset_id)
        .where(Generation.instruction_hash == instruction_hash)
        .where(Generation.model == model)
        .where(Generation.prompt_version == prompt_version)
        .where(Generation.status == "success")
        .order_by(Generation.created_at.desc(), Generation.id.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def find_original_path(
    db: AsyncSession,
    *,
    image_hash: str,
) -> str | None:
    """같은 이미지 해시의 기존 원본 파일이 남아 있으면 그 경로를 돌려준다."""
    stmt = (
        select(Generation.original_path)
        .where(Generation.image_hash == image_hash)
        .where(Generation.original_path.is_not(None))
        .order_by(Generation.created_at.desc(), Generation.id.desc())
    )
    result = await db.execute(stmt)
    for path in result.scalars():
        if not path:
            continue
        exists = await asyncio.to_thread(Path(path).is_file)
        if exists:
            return path
    return None


async def get_user_generation_by_request_id(
    db: AsyncSession,
    *,
    user_id: str,
    request_id: str,
) -> Generation | None:
    """사용자 본인의 생성 기록 1건을 request_id로 조회한다."""
    stmt = (
        select(Generation)
        .where(Generation.user_id == user_id)
        .where(Generation.request_id == request_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_pending_generation(
    db: AsyncSession,
    *,
    request_id: str,
    image_hash: str,
    preset_id: str,
    instruction_hash: str,
    prompt_version: str,
    model: str,
    original_path: str | None,
    prompt: str | None,
    text_model: str | None = None,
    user_id: str | None = None,
    user_copy: str | None = None,
    parent_id: int | None = None,
) -> Generation:
    """OpenAI 호출 전 'pending' 행을 먼저 만들어 실패해도 흔적이 남게 한다."""
    generation = Generation(
        request_id=request_id,
        user_id=user_id,
        parent_id=parent_id,
        image_hash=image_hash,
        preset_id=preset_id,
        instruction_hash=instruction_hash,
        prompt_version=prompt_version,
        model=model,
        text_model=text_model,
        original_path=original_path,
        output_path=None,
        image_url=None,
        prompt=prompt,
        user_copy=user_copy,
        status="pending",
        error_message=None,
    )
    db.add(generation)
    await db.flush()
    return generation


async def mark_generation_success(
    db: AsyncSession,
    *,
    request_id: str,
    output_path: str,
    image_url: str | None,
) -> Generation:
    """pending 행을 success로 갱신하고 결과 경로·URL을 채워 넣는다."""
    result = await db.execute(select(Generation).where(Generation.request_id == request_id))
    generation = result.scalar_one()
    generation.output_path = output_path
    generation.image_url = image_url
    generation.status = "success"
    generation.error_message = None
    await db.flush()
    return generation


async def mark_generation_failed(
    db: AsyncSession,
    *,
    request_id: str,
    error_message: str,
) -> Generation:
    """pending 행을 failed로 갱신하고 실패 사유를 기록한다."""
    result = await db.execute(select(Generation).where(Generation.request_id == request_id))
    generation = result.scalar_one()
    generation.status = "failed"
    generation.error_message = error_message
    await db.flush()
    return generation


async def create_cached_generation(
    db: AsyncSession,
    *,
    request_id: str,
    image_hash: str,
    preset_id: str,
    instruction_hash: str,
    prompt_version: str,
    model: str,
    original_path: str | None,
    output_path: str | None,
    image_url: str | None,
    prompt: str | None,
    text_model: str | None = None,
    user_id: str | None = None,
    user_copy: str | None = None,
    parent_id: int | None = None,
) -> Generation:
    """캐시 hit을 'cached' 행으로 남긴다. user_id·parent_id는 이번 요청 값을 저장한다."""
    generation = Generation(
        request_id=request_id,
        user_id=user_id,
        parent_id=parent_id,
        image_hash=image_hash,
        preset_id=preset_id,
        instruction_hash=instruction_hash,
        prompt_version=prompt_version,
        model=model,
        text_model=text_model,
        original_path=original_path,
        output_path=output_path,
        image_url=image_url,
        prompt=prompt,
        user_copy=user_copy,
        status="cached",
        error_message=None,
    )
    db.add(generation)
    await db.flush()
    return generation
