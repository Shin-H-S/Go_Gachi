import hashlib
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Generation

_WHITESPACE_RE = re.compile(r"\s+")


def image_sha256(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def normalize_instruction(feedback: str | None) -> str:
    if not feedback:
        return ""
    stripped = feedback.strip()
    return _WHITESPACE_RE.sub(" ", stripped) if stripped else ""


def instruction_sha256(feedback: str | None) -> str:
    normalized = normalize_instruction(feedback)
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
    for generation in result.scalars():
        if generation.output_path and Path(generation.output_path).exists():
            return generation
    return None


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
    user_id: str | None = None,
    parent_id: int | None = None,
) -> Generation:
    generation = Generation(
        request_id=request_id,
        user_id=user_id,
        parent_id=parent_id,
        image_hash=image_hash,
        preset_id=preset_id,
        instruction_hash=instruction_hash,
        prompt_version=prompt_version,
        model=model,
        original_path=original_path,
        output_path=None,
        image_url=None,
        prompt=prompt,
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
    user_id: str | None = None,
    parent_id: int | None = None,
) -> Generation:
    generation = Generation(
        request_id=request_id,
        user_id=user_id,
        parent_id=parent_id,
        image_hash=image_hash,
        preset_id=preset_id,
        instruction_hash=instruction_hash,
        prompt_version=prompt_version,
        model=model,
        original_path=original_path,
        output_path=output_path,
        image_url=image_url,
        prompt=prompt,
        status="cached",
        error_message=None,
    )
    db.add(generation)
    await db.flush()
    return generation
