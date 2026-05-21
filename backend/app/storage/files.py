"""파일 저장 — 업로드 사진을 검증한 뒤 uploads/ 에 저장한다."""

import io
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image

from app.core import config

# 허용 이미지 포맷(Pillow 가 인식하는 실제 포맷) → 서버가 부여하는 확장자
ALLOWED_FORMATS: dict[str, str] = {
    "PNG": ".png",
    "JPEG": ".jpg",  # jpg/jpeg 모두 Pillow 는 "JPEG" 로 인식
    "WEBP": ".webp",
}

# 업로드 최대 크기 (10MB)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def _make_filename(ext: str) -> str:
    """충돌 없는 저장 파일명을 만든다. (확장자는 서버가 결정한 값)

    Args:
        ext: 서버가 결정한 파일 확장자 (예: ".png").
    Returns:
        '20260521_153012_a1b2c3d4.png' 형식의 파일명.
    """
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{uuid.uuid4().hex[:8]}{ext}"


async def save_upload(image: UploadFile) -> Path:
    """업로드 파일이 진짜 이미지인지 검증한 뒤 uploads/ 에 저장한다.

    클라이언트가 보낸 헤더(content-type)·파일명을 신뢰하지 않는다.
    Pillow 로 실제 디코딩하여 이미지인지 확인하고, 확장자도 서버가 결정한다.

    Args:
        image: 업로드된 이미지 파일.
    Returns:
        저장된 파일의 경로.
    Raises:
        HTTPException: 유효한 이미지가 아니거나 허용되지 않은 형식일 때 (400).
    """
    data = await image.read()

    # 0) 실제 크기 재검증 (image.size 가 None 일 수도 있어 바이트로 직접 확인)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="파일이 너무 큽니다 (최대 10MB).")

    # 1) 진짜 이미지인지 디코딩으로 검증 (헤더/확장자 안 믿음)
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format  # 실제 포맷 (PNG/JPEG/WEBP ...)
        img.verify()  # 손상/위조 검사
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="유효한 이미지 파일이 아닙니다 (png/jpg/webp 만 허용).",
        )

    # 2) 허용 포맷만 통과 + 확장자는 서버가 결정 (클라 파일명 무시)
    if fmt not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 이미지 형식입니다: {fmt} (png/jpg/webp 만 허용).",
        )
    ext = ALLOWED_FORMATS[fmt]

    # 3) 저장
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = config.UPLOAD_DIR / _make_filename(ext)
    dest.write_bytes(data)
    return dest


def save_result(image_bytes: bytes, ext: str = ".png") -> Path:
    """생성된 결과 이미지를 outputs/ 폴더에 저장한다.

    Args:
        image_bytes: 생성된 이미지의 바이트 데이터.
        ext: 파일 확장자 (기본 .png).
    Returns:
        저장된 결과 이미지의 경로.
    """
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = config.OUTPUT_DIR / f"result_{stamp}_{uuid.uuid4().hex[:8]}{ext}"
    dest.write_bytes(image_bytes)
    return dest
