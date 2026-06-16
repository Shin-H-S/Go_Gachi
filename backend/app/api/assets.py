"""저장된 이미지 파일 다운로드 API."""

from __future__ import annotations

import mimetypes
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from backend.app.core.auth import AuthUser, get_current_user
from backend.app.core.config import get_settings
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.services.storage import get_storage

router = APIRouter(prefix="/api/assets", tags=["assets"])
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]


class DownloadUrlResponse(BaseModel):
    download_url: str = Field(alias="downloadUrl")
    expires_in: int = Field(alias="expiresIn")


@router.post(
    "/generations/{request_id}/download-url",
    response_model=DownloadUrlResponse,
    response_model_by_alias=True,
)
async def create_generation_download_url(
    request_id: str,
    user: CurrentUser,
) -> DownloadUrlResponse:
    """로그인 사용자 본인의 생성 결과 다운로드 URL을 발급한다."""
    settings = get_settings()
    generation = await _get_downloadable_generation(request_id=request_id, user_id=user.id)
    storage = get_storage(settings)
    filename = _filename(generation.output_path)
    content_type = _content_type(filename)
    signed_url = await storage.download_url(
        generation.output_path,
        filename=filename,
        content_type=content_type,
        expires_in=settings.download_url_ttl_seconds,
    )
    return DownloadUrlResponse(
        downloadUrl=signed_url or f"/api/assets/generations/{request_id}/download",
        expiresIn=settings.download_url_ttl_seconds,
    )


@router.get("/generations/{request_id}/download")
async def download_generation_asset(
    request_id: str,
    user: CurrentUser,
) -> Response:
    """local 저장소의 생성 결과 파일을 로그인 사용자에게 내려준다."""
    settings = get_settings()
    generation = await _get_downloadable_generation(request_id=request_id, user_id=user.id)
    storage = get_storage(settings)
    body = await storage.read_bytes(generation.output_path)
    if body is None:
        raise HTTPException(status_code=404, detail="asset not found")
    filename = _filename(generation.output_path)
    return Response(
        content=body,
        media_type=_content_type(filename),
        headers={"Content-Disposition": _content_disposition(filename)},
    )


async def _get_downloadable_generation(*, request_id: str, user_id: str):
    async with async_session_scope() as db:
        generation = await crud.get_downloadable_user_generation(
            db,
            user_id=user_id,
            request_id=request_id,
        )
    if generation is None:
        raise HTTPException(status_code=404, detail="asset not found")
    return generation


def _filename(path: str | None) -> str:
    if not path:
        raise HTTPException(status_code=404, detail="asset not found")
    filename = path.replace("\\", "/").rsplit("/", 1)[-1]
    if not filename:
        raise HTTPException(status_code=404, detail="asset not found")
    return filename


def _content_type(filename: str) -> str:
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def _content_disposition(filename: str) -> str:
    quoted = quote(filename)
    return f"attachment; filename={quoted}; filename*=UTF-8''{quoted}"
