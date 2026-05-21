"""이미지 검증·크기 계산·리사이즈 도우미.

'품질검사원 + 재단사' 역할. 들어온 사진이 유효한지 검사하고(validate_upload),
게시 위치에 맞는 크기를 정하고(resolve_target_size), 결과물을 그 크기로 잘라(fit_to_size)
파일로 저장(save_png)한다.
"""

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
    """게시 위치에 맞는 최종 이미지 크기를 정한다.

    Args:
        placement: 게시 위치(인스타 피드 등). custom 이면 아래 두 값을 쓴다.
        custom_width: 사용자 지정 가로(placement=custom 일 때 필수).
        custom_height: 사용자 지정 세로(placement=custom 일 때 필수).
    Returns:
        ImageSize: 결정된 가로/세로 픽셀.
    Raises:
        ValueError: custom 인데 가로/세로가 안 들어온 경우.
    """
    if placement == Placement.CUSTOM:
        # custom은 프론트에서 직접 입력한 사이즈가 있어야 합니다.
        if not custom_width or not custom_height:
            raise ValueError("custom placement requires custom_width and custom_height")
        return ImageSize(width=custom_width, height=custom_height)
    return PLACEMENT_SIZES[placement]


def validate_upload(content_type: str | None, file_bytes: bytes) -> None:
    """업로드 파일이 허용 타입·용량·실제 이미지인지 검사한다(문제 있으면 ValueError).

    돈이 드는 OpenAI 호출 '전에' 막아 비용과 시간을 아끼는 게 목적이다.

    Args:
        content_type: 업로드 MIME 타입(예: image/jpeg).
        file_bytes: 업로드 파일 전체 바이트.
    Raises:
        ValueError: 허용 안 된 형식, 용량 초과, 또는 깨진 이미지일 때.
    """
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
    """OpenAI 결과 이미지를 목표 크기에 맞게 중앙 기준으로 자르고 리사이즈한다.

    Args:
        image_bytes: OpenAI 가 돌려준 이미지 바이트.
        size: 최종 목표 크기.
    Returns:
        목표 크기에 정확히 맞춰진 RGB 이미지 객체.
    """
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
    """이미지를 지정 경로에 PNG로 저장한다(상위 폴더가 없으면 만든다).

    Args:
        image: 저장할 이미지 객체.
        output_path: 저장할 파일 경로.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
