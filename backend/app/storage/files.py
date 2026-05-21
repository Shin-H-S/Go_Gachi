"""파일 이름 짓기·저장·URL 생성 도우미('창고지기' 역할)."""

from pathlib import Path
from uuid import uuid4

from app.core.config import settings


def new_request_id() -> str:
    """요청 한 건을 식별할 고유 ID를 만든다(원본/결과 파일명을 이 ID로 맞춘다)."""
    # 요청 단위로 원본/결과 파일명을 맞추기 위한 고유 ID입니다.
    return uuid4().hex


def extension_from_content_type(content_type: str | None) -> str:
    """MIME 타입을 파일 확장자로 바꾼다(알 수 없으면 .bin).

    Args:
        content_type: 업로드 MIME 타입(예: image/png).
    Returns:
        앞에 점이 붙은 확장자 문자열(예: ".png").
    """
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }.get(content_type or "", ".bin")


def save_upload(file_bytes: bytes, content_type: str | None, request_id: str) -> Path:
    """업로드 원본 사진을 backend/uploads 아래에 저장한다.

    Args:
        file_bytes: 업로드 파일 바이트.
        content_type: MIME 타입(확장자 결정에 사용).
        request_id: 파일명에 쓸 요청 ID.
    Returns:
        저장된 파일 경로.
    """
    # 업로드 파일은 backend/uploads 아래에 저장하고, 실제 이미지는 .gitignore로 제외합니다.
    settings.ensure_directories()
    path = (
        settings.UPLOAD_DIR / f"{request_id}{extension_from_content_type(content_type)}"
    )
    path.write_bytes(file_bytes)
    return path


def output_path(request_id: str) -> Path:
    """결과 이미지를 저장할 경로(backend/outputs/<id>.png)를 만든다."""
    settings.ensure_directories()
    return settings.OUTPUT_DIR / f"{request_id}.png"


def output_url(filename: str) -> str:
    """결과 파일명을 프론트가 접근할 정적 URL(/outputs/<파일명>)로 바꾼다."""
    # main.py에서 mount한 정적 경로와 맞춰 프론트가 접근할 URL을 만듭니다.
    return f"/outputs/{filename}"
