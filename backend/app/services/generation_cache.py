"""이미지 생성 캐시 조회와 cache hit 응답 처리."""

import asyncio
import base64
import logging
from typing import TypedDict

from backend.app.core.config import Settings
from backend.app.core.logging_utils import short_id
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.db.models import Generation
from backend.app.services.storage import get_storage
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
    target_bytes: bytes


def _snapshot(row: Generation, target_bytes: bytes) -> CacheSnapshot:
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
        "target_bytes": target_bytes,
    }


async def find_cache_snapshot(
    *,
    settings: Settings,
    image_hash: str,
    preset_id: str,
    instruction_hash: str,
    model: str,
    prompt_version: str,
) -> CacheSnapshot | None:
    """세션 밖에서도 안전하게 쓸 수 있도록 캐시 row의 필요한 값만 복사한다."""
    async with async_session_scope() as db:
        rows = await crud.list_cached_generations(
            db,
            image_hash=image_hash,
            preset_id=preset_id,
            instruction_hash=instruction_hash,
            model=model,
            prompt_version=prompt_version,
        )
    for row in rows:
        if row.output_path is None:
            continue
        target_bytes = await _load_cached_bytes(row.output_path, settings)
        if target_bytes is not None:
            return _snapshot(row, target_bytes)
    return None


async def _load_cached_bytes(output_path: str, settings: Settings) -> bytes | None:
    """현재 storage backend에서 캐시 결과 이미지를 읽는다."""
    storage = get_storage(settings)
    try:
        return await storage.read_bytes(output_path)
    except Exception:
        logger.exception("cache hit storage read failed path=%s", output_path)
        return None


async def cached_response(
    snapshot: CacheSnapshot | None,
    *,
    generation_id: str,
    settings: Settings,
    user_id: str | None,
    user_copy: str | None,
    text_model: str | None,
    text_cost_usd: float,
) -> dict[str, str | None] | None:
    """캐시가 있으면 cached row와 비용 0 사용 row를 기록하고 응답을 만든다."""
    if snapshot is None or snapshot["output_path"] is None:
        return None

    encoded = await asyncio.to_thread(base64.b64encode, snapshot["target_bytes"])
    image_data_url = f"data:image/png;base64,{encoded.decode('ascii')}"
    image_url = output_url(snapshot["output_path"])
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
            text_model=text_model,
            user_id=user_id,
            user_copy=user_copy,
        )
        await crud.record_usage(
            db,
            request_id=generation_id,
            image_model=snapshot["model"],
            text_model=text_model,
            image_cost_usd=0.0,
            text_cost_usd=text_cost_usd,
            cached=True,
        )
    return {
        "image_data_url": image_data_url,
        "image_url": image_url,
        "provider": "openai",
        "note": "캐시된 결과 재사용",
        "prompt": snapshot["prompt"],
    }
