"""이미지 생성 서비스 호환용 진입점.

실제 구현은 역할별 모듈에 나뉘어 있다. 기존 코드와 테스트가
`backend.app.services.image_edit`를 import하던 흐름은 유지한다.
"""

from backend.app.services.generation_service import edit_image
from backend.app.services.image_processing import normalize_for_openai, render_target_png
from backend.app.services.image_types import ImageInfo, ResizeMode, TargetSize, UploadedImage
from backend.app.services.image_validation import (
    SUPPORTED_UPLOAD_LABEL,
    SUPPORTED_UPLOAD_TYPES,
    parse_image,
)
from backend.app.services.openai_images import call_openai_edit

# 기존 테스트/사용처가 `_call_openai_edit` 이름을 참조할 수 있어 별칭을 남긴다.
_call_openai_edit = call_openai_edit

__all__ = [
    "ImageInfo",
    "ResizeMode",
    "SUPPORTED_UPLOAD_LABEL",
    "SUPPORTED_UPLOAD_TYPES",
    "TargetSize",
    "UploadedImage",
    "_call_openai_edit",
    "call_openai_edit",
    "edit_image",
    "normalize_for_openai",
    "parse_image",
    "render_target_png",
]
