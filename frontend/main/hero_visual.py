from html import escape
from pathlib import Path

from frontend.media.image_data import bytes_to_data_url

MAIN_SLIDE_ASSET_DIR = (
    Path(__file__).resolve().parents[1] / "assets" / "main" / "optimized"
)
MAIN_HERO_SLIDES = (
    {
        "filename": "main-slide-01.webp",
        "eyebrow": "\ub2f9\uadfc\ub9c8\ucf13",
        "title": "\uba54\ub274 \uc774\ubbf8\uc9c0",
        "alt": "\ub2f9\uadfc\ub9c8\ucf13 \uba54\ub274 \uc774\ubbf8\uc9c0 \ubbf8\ub9ac\ubcf4\uae30",
        "class_name": "blue-panel-one",
    },
    {
        "filename": "main-slide-02.webp",
        "eyebrow": "\uc778\uc2a4\ud0c0\uadf8\ub7a8",
        "title": "\uc815\uc0ac\uac01\ud615 \ud53c\ub4dc",
        "alt": (
            "\uc778\uc2a4\ud0c0\uadf8\ub7a8 \uc815\uc0ac\uac01\ud615 "
            "\ud53c\ub4dc \uc774\ubbf8\uc9c0 \ubbf8\ub9ac\ubcf4\uae30"
        ),
        "class_name": "blue-panel-two",
    },
    {
        "filename": "main-slide-03.webp",
        "eyebrow": "\ub2f9\uadfc\ub9c8\ucf13",
        "title": "\uba54\ub274 \uc774\ubbf8\uc9c0",
        "alt": "\ub2f9\uadfc\ub9c8\ucf13 \uba54\ub274 \uc774\ubbf8\uc9c0 \ubbf8\ub9ac\ubcf4\uae30",
        "class_name": "blue-panel-three",
    },
    {
        "filename": "main-slide-04.webp",
        "eyebrow": "\ubc30\ub2ec\uc758 \ubbfc\uc871",
        "title": "\ub2e8\uc0c9 \ubc30\uacbd \uc774\ubbf8\uc9c0",
        "alt": (
            "\ubc30\ub2ec\uc758 \ubbfc\uc871 \ub2e8\uc0c9 "
            "\ubc30\uacbd \uc774\ubbf8\uc9c0 \ubbf8\ub9ac\ubcf4\uae30"
        ),
        "class_name": "blue-panel-four",
    },
    {
        "filename": "main-slide-05.webp",
        "eyebrow": "\uc778\uc2a4\ud0c0\uadf8\ub7a8",
        "title": "\uc815\uc0ac\uac01\ud615 \ud53c\ub4dc",
        "alt": (
            "\uc778\uc2a4\ud0c0\uadf8\ub7a8 \uc815\uc0ac\uac01\ud615 "
            "\ud53c\ub4dc \uc774\ubbf8\uc9c0 \ubbf8\ub9ac\ubcf4\uae30"
        ),
        "class_name": "blue-panel-five",
    },
)


def main_slide_image_src(filename: str) -> str:
    return bytes_to_data_url((MAIN_SLIDE_ASSET_DIR / filename).read_bytes(), "image/webp")


def build_hero_visual_html() -> str:
    panels = []
    loop_slides = (*MAIN_HERO_SLIDES, MAIN_HERO_SLIDES[0])

    for index, slide in enumerate(loop_slides):
        filename = str(slide["filename"])
        class_name = escape(str(slide["class_name"]))
        eyebrow = escape(str(slide["eyebrow"]))
        title = escape(str(slide["title"]))
        alt = escape(str(slide["alt"]))
        loading = "eager" if index == 0 else "lazy"
        image_src = main_slide_image_src(filename)

        panels.append(
            "\n".join(
                (
                    f'<article class="blue-panel {class_name}">',
                    '<div class="blue-panel-image-stage">',
                    (
                        f'<img class="blue-panel-image" src="{image_src}" '
                        f'alt="{alt}" loading="{loading}" />'
                    ),
                    "</div>",
                    '<div class="blue-panel-caption">',
                    f"<span>{eyebrow}</span>",
                    f"<strong>{title}</strong>",
                    "</div>",
                    "</article>",
                )
            )
        )

    slides_html = "\n".join(panels)
    return "\n".join(
        (
            '<section class="hero-visual" aria-label="Go Gachi AI ad preview carousel">',
            '<div class="blue-slide-window">',
            '<div class="blue-slide-track">',
            slides_html,
            "</div>",
            "</div>",
            "</section>",
        )
    )
