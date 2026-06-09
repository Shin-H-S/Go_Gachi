"""광고 문구를 최종 이미지 위에 합성하는 후처리 서비스."""

import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from backend.app.core.config import ROOT_DIR, Settings
from backend.app.core.text_layouts import TextLayout
from backend.app.services.copywriting import AdCopy

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _TextLine:
    """실제 렌더링할 한 줄의 문구와 측정값."""

    text: str
    font: ImageFont.ImageFont
    width: int
    height: int


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    """#RRGGBB 색상 문자열을 Pillow가 쓰는 RGB 튜플로 바꾼다."""
    clean = value.strip().lstrip("#")
    if len(clean) != 6:
        return (255, 255, 255)
    try:
        return tuple(int(clean[index : index + 2], 16) for index in (0, 2, 4))
    except ValueError:
        return (255, 255, 255)


def _configured_font_paths(settings: Settings, *, bold: bool) -> list[Path]:
    """환경변수와 흔한 시스템 경로에서 사용할 수 있는 폰트 후보를 만든다."""
    paths: list[Path] = []

    if bold and settings.text_font_bold_path:
        paths.append(settings.text_font_bold_path)
    if not bold and settings.text_font_regular_path:
        paths.append(settings.text_font_regular_path)

    # 실제 폰트 선택은 별도 논의 대상이므로, 여기서는 나중에 파일만 넣으면 잡히는 경로를 열어둔다.
    asset_names = (
        ("Pretendard-Bold.otf", "Pretendard-Regular.otf")
        if bold
        else ("Pretendard-Regular.otf", "Pretendard-Bold.otf")
    )
    windows_names = ("malgunbd.ttf", "malgun.ttf") if bold else ("malgun.ttf", "malgunbd.ttf")
    linux_paths = (
        (
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        )
        if bold
        else (
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        )
    )
    paths.extend(
        ROOT_DIR / "backend" / "app" / "assets" / "fonts" / asset_name
        for asset_name in asset_names
    )
    paths.extend(Path("C:/Windows/Fonts") / font_name for font_name in windows_names)
    paths.extend(linux_paths)
    return paths


def _load_font(settings: Settings, size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    """사용 가능한 폰트를 찾고, 없으면 Pillow 기본 폰트로 후퇴한다."""
    for path in _configured_font_paths(settings, bold=bold):
        if not path.exists():
            continue
        try:
            return ImageFont.truetype(str(path), size=size)
        except OSError:
            logger.warning("text font could not be loaded path=%s", path)

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _measure(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
) -> tuple[int, int] | None:
    """폰트가 문구를 렌더링할 수 있는지 확인하며 크기를 잰다."""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
    except UnicodeEncodeError:
        return None
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str | None,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[_TextLine] | None:
    """한글/영문을 모두 고려해 글자 단위로 안전하게 줄바꿈한다."""
    clean_text = " ".join((text or "").split())
    if not clean_text or max_lines <= 0:
        return []

    lines: list[_TextLine] = []
    current = ""
    for char in clean_text:
        candidate = current + char
        measured = _measure(draw, candidate, font)
        if measured is None:
            return None
        if measured[0] <= max_width or not current:
            current = candidate
            continue

        current_size = _measure(draw, current, font)
        if current_size is None:
            return None
        lines.append(_TextLine(current, font, current_size[0], current_size[1]))
        current = char
        if len(lines) >= max_lines:
            return lines

    if current and len(lines) < max_lines:
        current_size = _measure(draw, current, font)
        if current_size is None:
            return None
        lines.append(_TextLine(current, font, current_size[0], current_size[1]))
    return lines


def _build_lines(
    draw: ImageDraw.ImageDraw,
    ad_copy: AdCopy,
    layout: TextLayout,
    settings: Settings,
    image_height: int,
    max_width: int,
) -> list[_TextLine] | None:
    """문구 구조를 실제 렌더링 라인 목록으로 변환한다."""
    headline_font = _load_font(
        settings,
        max(18, round(image_height * layout.headline_font_ratio)),
        bold=True,
    )
    subcopy_font = _load_font(
        settings,
        max(14, round(image_height * layout.subcopy_font_ratio)),
    )
    cta_font = _load_font(
        settings,
        max(14, round(image_height * layout.cta_font_ratio)),
        bold=True,
    )

    line_budget = layout.max_lines
    lines: list[_TextLine] = []
    for text, font in (
        (ad_copy.headline, headline_font),
        (ad_copy.subcopy, subcopy_font),
        (ad_copy.cta, cta_font),
    ):
        wrapped = _wrap_text(draw, text, font, max_width, line_budget)
        if wrapped is None:
            return None
        lines.extend(wrapped)
        line_budget -= len(wrapped)
        if line_budget <= 0:
            break
    return lines


def _block_origin(
    image_size: tuple[int, int],
    block_size: tuple[int, int],
    layout: TextLayout,
) -> tuple[int, int]:
    """레이아웃 위치 키워드를 실제 좌표로 바꾼다."""
    image_width, image_height = image_size
    block_width, block_height = block_size
    margin = layout.safe_margin

    if layout.position == "top_left":
        x = margin
    else:
        x = (image_width - block_width) // 2

    if layout.position.startswith("top"):
        y = margin
    else:
        y = image_height - block_height - margin

    return max(margin // 2, x), max(margin // 2, y)


def _draw_backdrop(
    overlay: Image.Image,
    box: tuple[int, int, int, int],
    text_color: tuple[int, int, int],
) -> None:
    """복잡한 배경 위에서도 문구가 읽히도록 반투명 배경을 깐다."""
    draw = ImageDraw.Draw(overlay)
    brightness = sum(text_color) / 3
    fill = (0, 0, 0, 110) if brightness > 160 else (255, 255, 255, 170)
    radius = max(10, (box[2] - box[0]) // 28)
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def render_text_overlay(
    content: bytes,
    ad_copy: AdCopy,
    layout: TextLayout,
    settings: Settings,
) -> bytes:
    """PNG 이미지 바이트 위에 광고 문구를 합성해 다시 PNG 바이트로 반환한다."""
    with Image.open(BytesIO(content)) as source:
        image = source.convert("RGBA")

    draw_probe = ImageDraw.Draw(image)
    image_width, image_height = image.size
    max_width = max(1, round(image_width * layout.max_width_ratio))
    lines = _build_lines(draw_probe, ad_copy, layout, settings, image_height, max_width)
    if lines is None:
        logger.warning("text overlay skipped because current font cannot render copy")
        return content
    if not lines:
        return content

    line_gap = max(6, round(image_height * 0.01))
    block_width = min(max_width, max(line.width for line in lines))
    block_height = sum(line.height for line in lines) + line_gap * (len(lines) - 1)
    block_x, block_y = _block_origin(
        image.size,
        (block_width, block_height),
        layout,
    )
    padding = max(14, round(min(image_width, image_height) * 0.02))
    color = _hex_to_rgb(layout.color)

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    if layout.backdrop:
        _draw_backdrop(
            overlay,
            (
                max(0, block_x - padding),
                max(0, block_y - padding),
                min(image_width, block_x + block_width + padding),
                min(image_height, block_y + block_height + padding),
            ),
            color,
        )

    draw = ImageDraw.Draw(overlay)
    y = block_y
    shadow_offset = max(2, round(image_height * 0.003))
    for line in lines:
        if layout.align == "center":
            x = block_x + (block_width - line.width) // 2
        else:
            x = block_x

        if layout.shadow:
            draw.text(
                (x + shadow_offset, y + shadow_offset),
                line.text,
                font=line.font,
                fill=(0, 0, 0, 150),
            )
        draw.text((x, y), line.text, font=line.font, fill=(*color, 255))
        y += line.height + line_gap

    rendered = Image.alpha_composite(image, overlay).convert("RGB")
    output = BytesIO()
    rendered.save(output, format="PNG", optimize=True)
    return output.getvalue()
