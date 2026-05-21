"""Image validation and resizing helpers."""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings
from app.models.schemas import ImageSize, Placement


PLACEMENT_SIZES: dict[Placement, ImageSize] = {
    # MVP 단계에서는 대표 플랫폼 규격을 고정 프리셋으로 관리합니다.
    Placement.INSTAGRAM_FEED: ImageSize(width=1080, height=1080),
    Placement.INSTAGRAM_STORY: ImageSize(width=1080, height=1920),
    Placement.INSTAGRAM_REELS: ImageSize(width=1080, height=1920),
    Placement.FACEBOOK_FEED: ImageSize(width=1200, height=1500),
    Placement.NAVER_PLACE: ImageSize(width=1080, height=1080),
    Placement.NAVER_BLOG: ImageSize(width=1200, height=628),
    Placement.KAKAO_CHANNEL: ImageSize(width=1080, height=1080),
    Placement.BANNER_LANDSCAPE: ImageSize(width=1200, height=628),
}


def resolve_target_size(
    placement: Placement,
    custom_width: int | None = None,
    custom_height: int | None = None,
) -> ImageSize:
    if placement == Placement.CUSTOM:
        # custom은 프론트에서 직접 입력한 사이즈가 있어야 합니다.
        if not custom_width or not custom_height:
            raise ValueError("custom placement requires custom_width and custom_height")
        return ImageSize(width=custom_width, height=custom_height)
    return PLACEMENT_SIZES[placement]


def validate_upload(content_type: str | None, file_bytes: bytes) -> None:
    # API 비용이 드는 OpenAI 호출 전에 파일 타입, 용량, 이미지 유효성을 먼저 확인합니다.
    if content_type not in settings.ALLOWED_IMAGE_CONTENT_TYPES:
        allowed = ", ".join(settings.ALLOWED_IMAGE_CONTENT_TYPES)
        raise ValueError(f"unsupported image type. allowed: {allowed}")
    if len(file_bytes) > settings.max_upload_bytes:
        raise ValueError(f"image is larger than {settings.MAX_UPLOAD_MB}MB")
    try:
        with Image.open(BytesIO(file_bytes)) as image:
            image.verify()
    except UnidentifiedImageError as exc:
        raise ValueError("uploaded file is not a valid image") from exc


def fit_to_size(image_bytes: bytes, size: ImageSize) -> Image.Image:
    # OpenAI 결과물을 최종 게시 위치에 맞게 중앙 기준으로 자르고 리사이즈합니다.
    with Image.open(BytesIO(image_bytes)) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        return ImageOps.fit(
            image,
            (size.width, size.height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )


def save_png(image: Image.Image, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
