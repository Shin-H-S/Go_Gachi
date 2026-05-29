import base64
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

try:
    from frontend.config import get_detail_size
except ModuleNotFoundError:
    from config import get_detail_size


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_names = ["malgunbd.ttf", "malgun.ttf"] if bold else ["malgun.ttf", "malgunbd.ttf"]
    candidates = [Path("C:/Windows/Fonts") / name for name in font_names]

    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)

    return ImageFont.load_default()


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def draw_gradient(image: Image.Image, start_hex: str, end_hex: str) -> None:
    width, height = image.size
    start = hex_to_rgb(start_hex)
    end = hex_to_rgb(end_hex)
    draw = ImageDraw.Draw(image)

    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(
            round(start[channel] * (1 - ratio) + end[channel] * ratio)
            for channel in range(3)
        )
        draw.line([(0, y), (width, y)], fill=color)


def rounded_paste(
    base: Image.Image,
    overlay: Image.Image,
    box: tuple[int, int],
    radius: int,
) -> None:
    overlay = overlay.convert("RGBA")
    mask = Image.new("L", overlay.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, overlay.width, overlay.height), radius=radius, fill=255)
    base.paste(overlay, box, mask)


def fit_image_cover(source: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    image = source.convert("RGB")
    return ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def fit_image_contain(source: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    image = source.convert("RGB")
    image.thumbnail(target_size, Image.Resampling.LANCZOS)
    return image


def make_preview_canvas(image_bytes: bytes, format_label: str, detail_label: str) -> bytes:
    target_size = get_detail_size(format_label, detail_label)
    canvas = Image.new("RGB", target_size, "#fbfaf4")
    image = fit_image_contain(Image.open(BytesIO(image_bytes)), target_size)
    x = (target_size[0] - image.width) // 2
    y = (target_size[1] - image.height) // 2
    canvas.paste(image, (x, y))

    output = BytesIO()
    canvas.save(output, format="PNG", optimize=True)
    return output.getvalue()


def wrap_text_by_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int,
) -> list[str]:
    clean_text = " ".join(text.strip().split())
    if not clean_text:
        return []

    lines: list[str] = []
    current = ""
    for char in clean_text:
        candidate = current + char
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = char
            if len(lines) >= max_lines:
                break

    if current and len(lines) < max_lines:
        lines.append(current)

    return lines


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_gap: int,
    max_lines: int,
) -> int:
    x, y = xy
    lines = wrap_text_by_width(draw, text, font, max_width, max_lines)
    for line in lines:
        draw.text((x, y), line, fill=fill, font=font)
        bbox = draw.textbbox((x, y), line, font=font)
        y += bbox[3] - bbox[1] + line_gap
    return y


def create_mock_banner(
    image_bytes: bytes,
    prompt: str,
    format_label: str,
    detail_label: str,
) -> bytes:
    width, height = get_detail_size(format_label, detail_label)
    scale = min(width, height) / 1080

    background = Image.new("RGB", (width, height), "#f8f7f2")
    draw_gradient(background, "#f8f7f2", "#e8f3ef")
    banner = background.convert("RGBA")

    margin = int(width * 0.075)
    photo_source = Image.open(BytesIO(image_bytes))
    photo_box = (int(width * 0.25), int(height * 0.34), int(width * 0.50), int(height * 0.54))
    px, py, pw, ph = photo_box

    shadow = Image.new("RGBA", (pw + 60, ph + 60), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (30, 30, pw + 30, ph + 30),
        radius=int(34 * scale),
        fill=(35, 42, 39, 46),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(18 * scale)))
    banner.paste(shadow, (px - 30, py - 30), shadow)

    photo = fit_image_cover(photo_source, (pw, ph))
    rounded_paste(banner, photo, (px, py), radius=int(30 * scale))

    draw = ImageDraw.Draw(banner)
    draw.rounded_rectangle(
        (px, py, px + pw, py + ph),
        radius=int(30 * scale),
        outline=(255, 255, 255, 210),
        width=max(3, int(5 * scale)),
    )

    title_font = load_font(max(34, int(58 * scale)), bold=True)
    body_font = load_font(max(22, int(34 * scale)), bold=False)

    text_x = margin
    text_y = int(height * 0.10)
    text_width = int(width * 0.78)
    cursor_y = draw_wrapped_text(
        draw,
        (text_x, text_y),
        "프롬프트 기반 미리보기",
        title_font,
        "#202725",
        text_width,
        int(8 * scale),
        2,
    )
    cursor_y += int(18 * scale)
    draw_wrapped_text(
        draw,
        (text_x, cursor_y),
        prompt,
        body_font,
        "#202725",
        text_width,
        int(8 * scale),
        3,
    )

    draw.text(
        (margin, height - int(42 * scale)),
        "CAFE AD MAKER",
        fill=(32, 39, 37, 128),
        font=load_font(max(16, int(22 * scale)), bold=True),
    )

    output = BytesIO()
    banner.convert("RGB").save(output, format="PNG", optimize=True)
    return output.getvalue()


def bytes_to_data_url(image_bytes: bytes, mime_type: str = "image/png") -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"
