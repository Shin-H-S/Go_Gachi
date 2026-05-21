"""File naming and storage helpers."""

from pathlib import Path
from uuid import uuid4

from app.core.config import settings


def new_request_id() -> str:
    # 요청 단위로 원본/결과 파일명을 맞추기 위한 고유 ID입니다.
    return uuid4().hex


def extension_from_content_type(content_type: str | None) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }.get(content_type or "", ".bin")


def save_upload(file_bytes: bytes, content_type: str | None, request_id: str) -> Path:
    # 업로드 파일은 backend/uploads 아래에 저장하고, 실제 이미지는 .gitignore로 제외합니다.
    settings.ensure_directories()
    path = settings.UPLOAD_DIR / f"{request_id}{extension_from_content_type(content_type)}"
    path.write_bytes(file_bytes)
    return path


def output_path(request_id: str) -> Path:
    settings.ensure_directories()
    return settings.OUTPUT_DIR / f"{request_id}.png"


def output_url(filename: str) -> str:
    # main.py에서 mount한 정적 경로와 맞춰 프론트가 접근할 URL을 만듭니다.
    return f"/outputs/{filename}"
