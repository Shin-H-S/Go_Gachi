"""업로드 이미지 data URL 검증과 실제 이미지 정보 확인."""

import base64
import binascii
import re
from io import BytesIO

from PIL import Image

from backend.app.services.image_types import ImageInfo, UploadedImage

DATA_URL_PATTERN = re.compile(
    r"^data:(image/(?:png|jpe?g|webp));base64,([A-Za-z0-9+/=]+)$",
    re.IGNORECASE,
)
SUPPORTED_UPLOAD_TYPES = ("jpg", "jpeg", "png", "webp")
SUPPORTED_UPLOAD_LABEL = "JPG, PNG, WEBP"


def _detect_image_mime(content: bytes) -> str | None:
    """파일 시그니처로 실제 이미지 MIME을 판별한다."""
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    return None


def _inspect_image(content: bytes) -> ImageInfo:
    """Pillow로 실제 이미지를 열어 포맷·모드·크기를 확인한다."""
    try:
        with Image.open(BytesIO(content)) as image:
            # 애니메이션/멀티프레임 이미지도 첫 프레임 기준으로 처리한다.
            image.seek(0)
            image.load()
            return ImageInfo(
                format=str(image.format or "unknown"),
                mode=image.mode,
                width=image.width,
                height=image.height,
            )
    except Exception as exc:
        raise ValueError("이미지 파일을 열 수 없습니다.") from exc


def parse_image(data_url: str, max_upload_bytes: int) -> UploadedImage:
    """프론트가 보낸 data URL을 검증하고 이미지 바이트로 변환한다."""
    match = DATA_URL_PATTERN.match(data_url or "")
    if not match:
        raise ValueError(f"{SUPPORTED_UPLOAD_LABEL} 이미지만 업로드할 수 있습니다.")

    mime_type = match.group(1).lower().replace("image/jpg", "image/jpeg")
    try:
        # validate=True로 깨진 base64가 500이 아니라 사용자 입력 오류가 되게 한다.
        content = base64.b64decode(match.group(2), validate=True)
    except binascii.Error as exc:
        raise ValueError("이미지 데이터가 올바른 base64 형식이 아닙니다.") from exc

    if not content or len(content) > max_upload_bytes:
        raise ValueError("이미지는 50MB 이하만 업로드할 수 있습니다.")

    detected_mime = _detect_image_mime(content)
    if detected_mime is None:
        raise ValueError("이미지 파일 형식을 확인할 수 없습니다.")
    if detected_mime != mime_type:
        raise ValueError("이미지 MIME 타입과 실제 파일 형식이 일치하지 않습니다.")

    extension = "jpg" if mime_type == "image/jpeg" else mime_type.split("/")[-1]
    return UploadedImage(
        mime_type=mime_type,
        content=content,
        extension=extension,
        info=_inspect_image(content),
    )
