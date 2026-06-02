"""이미지 정규화와 최종 광고 규격 후처리."""

from io import BytesIO

from PIL import Image, ImageFilter, ImageOps

from backend.app.services.image_types import ImageInfo, ResizeMode, TargetSize, UploadedImage


def _to_rgb_image(source: Image.Image) -> Image.Image:
    """OpenAI 입력 안정성을 위해 모든 업로드 이미지를 RGB 이미지로 맞춘다."""
    image = ImageOps.exif_transpose(source)

    # 투명 채널이 있으면 흰 배경에 합성해 광고 이미지에서 예측 가능한 RGB로 만든다.
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        background.alpha_composite(rgba)
        return background.convert("RGB")

    return image.convert("RGB")


def normalize_for_openai(uploaded: UploadedImage) -> UploadedImage:
    """OpenAI 호출 전 입력 이미지를 표준 PNG/RGB로 정규화한다.

    브라우저와 Pillow가 열 수 있는 이미지라도 CMYK, 팔레트, 일부 WebP/EXIF 조합은
    OpenAI 이미지 편집 API에서 거절될 수 있어, 외부 API에는 항상 PNG/RGB만 보낸다.
    """
    with Image.open(BytesIO(uploaded.content)) as source:
        source.seek(0)
        image = _to_rgb_image(source)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    normalized = output.getvalue()
    return UploadedImage(
        mime_type="image/png",
        content=normalized,
        extension="png",
        info=ImageInfo(
            format="PNG",
            mode="RGB",
            width=image.width,
            height=image.height,
        ),
    )


def _render_cover(image: Image.Image, target_size: TargetSize) -> Image.Image:
    """캔버스를 꽉 채우고 남는 영역은 중앙 기준으로 잘라낸다."""
    return ImageOps.fit(
        image,
        (target_size.width, target_size.height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def _render_contain(image: Image.Image, target_size: TargetSize) -> Image.Image:
    """원본 전체가 보이도록 맞추고, 남는 영역은 흐림 배경으로 채운다."""
    canvas_size = (target_size.width, target_size.height)
    background = _render_cover(image, target_size)
    blur_radius = max(target_size.width, target_size.height) // 28
    background = background.filter(ImageFilter.GaussianBlur(max(8, blur_radius)))

    foreground = image.copy()
    foreground.thumbnail(canvas_size, Image.Resampling.LANCZOS)
    x = (target_size.width - foreground.width) // 2
    y = (target_size.height - foreground.height) // 2
    background.paste(foreground, (x, y))
    return background


def render_target_png(
    content: bytes,
    target_size: TargetSize,
    resize_mode: ResizeMode = "cover",
) -> bytes:
    """이미지 바이트를 선택한 상세 사이즈의 PNG로 정확히 맞춘다.

    OpenAI가 지원하는 생성 크기와 실제 광고 게시 규격은 다를 수 있으므로,
    모델 결과를 받은 뒤 선택한 리사이즈 정책으로 최종 픽셀 크기를 고정한다.
    """
    with Image.open(BytesIO(content)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        if resize_mode == "contain":
            fitted = _render_contain(image, target_size)
        else:
            fitted = _render_cover(image, target_size)

    output = BytesIO()
    fitted.save(output, format="PNG", optimize=True)
    return output.getvalue()
