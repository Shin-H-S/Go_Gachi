"""이미지 생성 흐름에서 필요한 저장 경로 결정과 저장 실행."""

from dataclasses import dataclass

from backend.app.core.config import Settings
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.services.image_types import UploadedImage
from backend.app.services.storage import get_storage


@dataclass(frozen=True)
class StoragePaths:
    """한 번의 생성 요청에서 사용할 원본/결과 저장 위치."""

    original_path: str
    output_path: str


async def prepare_storage(
    *,
    generation_id: str,
    image_hash: str,
    uploaded: UploadedImage,
    settings: Settings,
) -> StoragePaths:
    """원본 이미지 저장 위치와 결과 이미지 저장 위치를 준비한다."""
    storage = get_storage(settings)
    output_path = storage.output_path(generation_id)

    async with async_session_scope() as db:
        old_path = await crud.find_original_path(db, image_hash=image_hash)
    if old_path and await storage.exists(old_path):
        return StoragePaths(original_path=old_path, output_path=output_path)

    original_path = storage.original_path(
        image_hash=image_hash,
        extension=uploaded.extension,
        generation_id=generation_id,
    )
    await storage.write_bytes(
        original_path,
        body=uploaded.content,
        content_type=uploaded.mime_type,
    )
    return StoragePaths(original_path=original_path, output_path=output_path)


async def save_output(
    *,
    output_path: str,
    body: bytes,
    settings: Settings,
) -> None:
    """생성 결과 PNG를 현재 저장소에 저장한다."""
    storage = get_storage(settings)
    await storage.write_bytes(output_path, body=body, content_type="image/png")
