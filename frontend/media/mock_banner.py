from io import BytesIO

from PIL import Image, ImageDraw, ImageFilter

from frontend.core.config import get_detail_size
from frontend.media.image_common import (
    draw_gradient,
    draw_wrapped_text,
    fit_image_cover,
    load_font,
    rounded_paste,
)


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


