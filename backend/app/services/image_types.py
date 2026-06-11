"""이미지 생성 서비스에서 공유하는 타입 정의."""

from dataclasses import dataclass
from typing import Literal

ResizeMode = Literal["cover", "contain"]


@dataclass(frozen=True)
class ImageInfo:
    """업로드 이미지의 실제 디코딩 결과. OpenAI 실패 원인 추적에 사용한다."""

    format: str
    mode: str
    width: int
    height: int


@dataclass(frozen=True)
class UploadedImage:
    """OpenAI multipart 요청과 내부 이미지 처리에 필요한 업로드 이미지 정보."""

    mime_type: str
    content: bytes
    extension: str
    info: ImageInfo


@dataclass(frozen=True)
class TargetSize:
    """사용자가 최종으로 내려받을 이미지의 정확한 픽셀 크기."""

    width: int
    height: int
