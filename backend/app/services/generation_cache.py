"""이미지 생성 캐시 조회와 cache hit 응답 처리를 담당한다."""

import asyncio
import logging
from pathlib import Path
from typing import TypedDict

from backend.app.core.logging_utils import short_id
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.db.models import Generation
from backend.app.services.generation_files import file_to_data_url, new_generation_id
from backend.app.services.storage_url import output_url

logger = logging.getLogger(__name__)


class CacheSnapshot(TypedDict):
    image_hash: str
    preset_id: str
    instruction_hash: str
    prompt_version: str
    model: str
    original_path: str | None
    output_path: str | None
    image_url: str | None
    prompt: str | None


def _snapshot(row: Generation) -> CacheSnapshot:
    return {
        "image_hash": row.image_hash,
        "preset_id": row.preset_id,
        "instruction_hash": row.instruction_hash,
        "prompt_version": row.prompt_version,
        "model": row.model,
        "original_path": row.original_path,
        "output_path": row.output_path,
        "image_url": row.image_url,
        "prompt": row.prompt,
    }


async def find_cache_snapshot(
    *,
    image_hash: str,
    preset_id: str,
    instruction_hash: str,
    model: str,
    prompt_version: str,
) -> CacheSnapshot | None:
    """세션 밖에서도 안전하게 쓸 수 있도록 캐시 행의 필요한 값만 dict로 복사한다."""
    async with async_session_scope() as db:
        cached_row = await crud.find_cached_generation(
            db,
            image_hash=image_hash,
            preset_id=preset_id,
            instruction_hash=instruction_hash,
            model=model,
            prompt_version=prompt_version,
        )
        return None if cached_row is None else _snapshot(cached_row)


async def cached_response(
    snapshot: CacheSnapshot | None,
    *,
    user_id: str | None,
    user_copy: str | None,
    has_logo: bool,
    logo_position: str | None,
) -> dict[str, str | None] | None:
    """캐시 파일이 남아 있으면 cached 행과 비용 0 사용량을 기록하고 응답을 만든다."""
    if snapshot is None or snapshot["output_path"] is None:
        return None

    cached_path = Path(snapshot["output_path"])
    if not await asyncio.to_thread(cached_path.exists):
        return None

    image_data_url = await file_to_data_url(cached_path)
    image_url = output_url(cached_path)
    generation_id = new_generation_id()
    logger.info(
        "cache hit generation_id=%s image_hash=%s preset=%s user_id=%s",
        generation_id,
        short_id(snapshot["image_hash"]),
        snapshot["preset_id"],
        short_id(user_id),
    )
    async with async_session_scope() as db:
        await crud.create_cached_generation(
            db,
            request_id=generation_id,
            image_hash=snapshot["image_hash"],
            preset_id=snapshot["preset_id"],
            instruction_hash=snapshot["instruction_hash"],
            prompt_version=snapshot["prompt_version"],
            model=snapshot["model"],
            original_path=snapshot["original_path"],
            output_path=snapshot["output_path"],
            image_url=None,
            prompt=snapshot["prompt"],
            user_id=user_id,
            user_copy=user_copy,
            has_logo=has_logo,
            logo_position=logo_position,
            logo_image_hash=None,
            logo_storage_key=None,
        )
        await crud.record_usage(
            db,
            request_id=generation_id,
            model=snapshot["model"],
            operation="image_edit",
            estimated_cost=0.0,
            cached=True,
        )
    return {
        "image_data_url": image_data_url,
        "image_url": image_url,
        "provider": "openai",
        "note": "캐시된 결과 재사용",
        "prompt": snapshot["prompt"],
    }
