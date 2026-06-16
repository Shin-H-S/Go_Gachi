"""마이페이지 자료/폴더 관련 라우트."""

import asyncio
import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from backend.app.api.mypage_models import (
    FolderCreateRequest,
    FolderUpdateRequest,
    GenerationFolderRequest,
    _folder_item,
)
from backend.app.api.mypage_upload_data import _file_to_image_data_url
from backend.app.core.auth import AuthUser, get_current_user
from backend.app.core.logging_utils import short_id
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.db.models import Generation
from backend.app.services.storage_url import (
    output_download_url,
    output_url_if_exists_async,
    upload_url_if_exists_async,
)

router = APIRouter()
logger = logging.getLogger(__name__)
PAGE_SIZE = 12


async def _upload_item(row: Generation, used_count: int) -> dict[str, object] | None:
    if row.original_path is None:
        return None

    original_image_url = await upload_url_if_exists_async(row.original_path)
    if original_image_url is None:
        return None

    image_data_url = await _file_to_image_data_url(Path(row.original_path))

    return {
        "upload_id": row.image_hash,
        # /me/generations의 original_image_url과 같은 의미(업로드 원본 URL). 필드명 통일.
        "original_image_url": original_image_url,
        # DEPRECATED: 프론트가 original_image_url로 전환되면 후속 PR에서 제거.
        "image_data_url": image_data_url,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "used_count": used_count,
    }


@router.get("/me/generations")
async def read_my_generations(
    user: AuthUser = Depends(get_current_user),
    page: Annotated[int, Query(ge=1)] = 1,
) -> dict[str, object]:
    """현재 로그인한 사용자가 만든 생성 기록을 최신순으로 반환한다 ("내 작업 기록")."""
    offset = (page - 1) * PAGE_SIZE
    async with async_session_scope() as db:
        rows = await crud.list_user_generations(db, user.id, limit=PAGE_SIZE, offset=offset)
        total = await crud.count_user_generations(db, user.id)

    image_urls = await asyncio.gather(
        *(output_url_if_exists_async(row.output_path) for row in rows)
    )
    upload_urls = await asyncio.gather(
        *(upload_url_if_exists_async(row.original_path) for row in rows)
    )
    items = [
        {
            "request_id": row.request_id,
            "preset_id": row.preset_id,
            "folder_id": row.folder_id,
            "status": row.status,
            "image_url": image_url,
            "download_url": output_download_url(row.output_path) if image_url else None,
            "original_image_url": upload_url,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row, image_url, upload_url in zip(rows, image_urls, upload_urls, strict=True)
    ]
    logger.info(
        "my generations listed user_id=%s page=%d count=%d total=%d",
        short_id(user.id),
        page,
        len(items),
        total,
    )
    return {"items": items, "count": len(items), "total_count": total}


@router.get("/me/folders")
async def read_my_folders(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    """사용자가 만든 마이페이지 폴더 목록을 반환한다."""
    async with async_session_scope() as db:
        folders = await crud.list_user_folders(db, user.id)
        items = [_folder_item(folder) for folder in folders]
    return {"items": items, "count": len(items)}


@router.post("/me/folders", status_code=status.HTTP_201_CREATED)
async def create_my_folder(
    request: FolderCreateRequest,
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    """사용자가 만든 이미지 정리용 폴더를 추가한다."""
    try:
        async with async_session_scope() as db:
            folder = await crud.create_folder(db, user_id=user.id, name=request.name)
            item = _folder_item(folder)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="이미 같은 이름의 폴더가 있습니다.") from exc
    return item


@router.patch("/me/folders/{folder_id}")
async def rename_my_folder(
    folder_id: int,
    request: FolderUpdateRequest,
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    """사용자가 만든 폴더 이름을 변경한다."""
    try:
        async with async_session_scope() as db:
            folder = await crud.rename_folder(
                db,
                user_id=user.id,
                folder_id=folder_id,
                name=request.name,
            )
            if folder is None:
                raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")
            item = _folder_item(folder)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="이미 같은 이름의 폴더가 있습니다.") from exc
    return item


@router.delete("/me/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_folder(
    folder_id: int,
    user: AuthUser = Depends(get_current_user),
) -> None:
    """폴더만 삭제하고, 폴더 안 생성 이미지는 미분류로 이동한다."""
    async with async_session_scope() as db:
        deleted = await crud.delete_folder(db, user_id=user.id, folder_id=folder_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="폴더를 찾을 수 없습니다.")


@router.patch("/me/generations/{request_id}/folder")
async def update_generation_folder(
    request_id: str,
    request: GenerationFolderRequest,
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    """내 생성 이미지 1건을 폴더에 넣거나 미분류로 이동한다."""
    async with async_session_scope() as db:
        generation = await crud.set_generation_folder(
            db,
            user_id=user.id,
            request_id=request_id,
            folder_id=request.folder_id,
        )
        if generation is None:
            raise HTTPException(status_code=404, detail="작업 또는 폴더를 찾을 수 없습니다.")
        return {"request_id": generation.request_id, "folder_id": generation.folder_id}


@router.get("/me/uploads")
async def read_my_uploads(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    """마이페이지 업로드한 메뉴 사진 탭에 필요한 원본 이미지 목록을 반환한다."""
    async with async_session_scope() as db:
        rows = await crud.list_user_upload_generations(db, user.id)

    seen: set[str] = set()
    unique_rows: list[Generation] = []
    used_counts: dict[str, int] = {}
    for row in rows:
        used_counts[row.image_hash] = used_counts.get(row.image_hash, 0) + 1
        if row.image_hash in seen:
            continue
        seen.add(row.image_hash)
        unique_rows.append(row)

    maybe_items = await asyncio.gather(
        *(_upload_item(row, used_counts[row.image_hash]) for row in unique_rows)
    )
    items = [item for item in maybe_items if item is not None]
    return {"items": items, "count": len(items)}
