from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


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
            round(start[channel] * (1 - ratio) + end[channel] * ratio) for channel in range(3)
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
    image = ImageOps.exif_transpose(source).convert("RGB")
    return ImageOps.fit(image, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def fit_image_contain(source: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    image = ImageOps.exif_transpose(source).convert("RGB")
    image.thumbnail(target_size, Image.Resampling.LANCZOS)
    return image


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
