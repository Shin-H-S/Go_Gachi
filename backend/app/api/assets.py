"""저장된 이미지 파일 다운로드 라우트."""

import mimetypes
from pathlib import PurePosixPath
from typing import Annotated, Literal
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Path, Response

from backend.app.core.config import get_settings
from backend.app.services.storage import get_storage

router = APIRouter(prefix="/api/assets", tags=["assets"])
AssetKind = Literal["outputs", "uploads"]


@router.get("/download/{kind}/{filename}")
async def download_asset(
    kind: Annotated[AssetKind, Path()],
    filename: Annotated[str, Path(min_length=1)],
) -> Response:
    """이미지 파일을 브라우저 다운로드로 내려준다."""
    safe_filename = PurePosixPath(filename).name
    if safe_filename != filename or safe_filename in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="invalid filename")

    settings = get_settings()
    path = _storage_path(kind, safe_filename)
    body = await get_storage(settings).read_bytes(path)
    if body is None:
        raise HTTPException(status_code=404, detail="asset not found")

    media_type = mimetypes.guess_type(safe_filename)[0] or "application/octet-stream"
    quoted_filename = quote(safe_filename)
    return Response(
        content=body,
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f"attachment; filename={quoted_filename}; filename*=UTF-8''{quoted_filename}"
            )
        },
    )


def _storage_path(kind: AssetKind, filename: str) -> str:
    settings = get_settings()
    if settings.storage_backend == "r2":
        return f"{kind}/{filename}"
    if kind == "outputs":
        return str(settings.output_dir / filename)
    return str(settings.upload_dir / filename)
