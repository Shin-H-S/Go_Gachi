import importlib
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
STYLE_MAIN_VISUAL_FILE = ROOT_DIR / "frontend" / "css" / "main_visual.py"


def test_main_visual_html_uses_optimized_webp_slides(monkeypatch) -> None:
    hero_visual = importlib.import_module("frontend.main.hero_visual")
    monkeypatch.setattr(hero_visual, "main_slide_image_src", lambda filename: f"asset://{filename}")

    html = hero_visual.build_hero_visual_html()

    for index in range(1, 6):
        assert f"main-slide-{index:02d}.webp" in html
    assert html.count('<article class="blue-panel') == 6
    assert html.count('class="blue-panel-image"') == 6
    assert 'loading="eager"' in html
    assert 'loading="lazy"' in html


def test_main_visual_html_uses_korean_slide_captions(monkeypatch) -> None:
    hero_visual = importlib.import_module("frontend.main.hero_visual")
    monkeypatch.setattr(hero_visual, "main_slide_image_src", lambda filename: f"asset://{filename}")

    html = hero_visual.build_hero_visual_html()

    expected_pairs = (
        ("\ub2f9\uadfc\ub9c8\ucf13", "\uba54\ub274 \uc774\ubbf8\uc9c0"),
        ("\uc778\uc2a4\ud0c0\uadf8\ub7a8", "\uc815\uc0ac\uac01\ud615 \ud53c\ub4dc"),
        ("\ub2f9\uadfc\ub9c8\ucf13", "\uba54\ub274 \uc774\ubbf8\uc9c0"),
        ("\ubc30\ub2ec\uc758 \ubbfc\uc871", "\ub2e8\uc0c9 \ubc30\uacbd \uc774\ubbf8\uc9c0"),
        ("\uc778\uc2a4\ud0c0\uadf8\ub7a8", "\uc815\uc0ac\uac01\ud615 \ud53c\ub4dc"),
        ("\ub2f9\uadfc\ub9c8\ucf13", "\uba54\ub274 \uc774\ubbf8\uc9c0"),
    )
    assert tuple(re.findall(r"<span>(.*?)</span>\n<strong>(.*?)</strong>", html)) == expected_pairs
    for old_caption in (
        "Daangn Market",
        "Local menu card",
    ):
        assert old_caption not in html


def test_main_visual_html_does_not_render_as_markdown_code(monkeypatch) -> None:
    hero_visual = importlib.import_module("frontend.main.hero_visual")
    monkeypatch.setattr(hero_visual, "main_slide_image_src", lambda filename: f"asset://{filename}")

    html = hero_visual.build_hero_visual_html()

    assert html.startswith("<section")
    for line in html.splitlines():
        if line.strip():
            assert line == line.lstrip()


def test_main_visual_css_keeps_source_image_flat_and_clear() -> None:
    styles = STYLE_MAIN_VISUAL_FILE.read_text(encoding="utf-8")

    image_stage_block = styles.split(".blue-panel-image-stage {", 1)[1].split("}", 1)[0]
    image_stage_card_block = styles.split(".blue-panel-image-stage::before {", 1)[
        1
    ].split("}", 1)[0]
    image_block = styles.split(".blue-panel-image {", 1)[1].split("}", 1)[0]
    panel_overlay_block = styles.split(".blue-panel::before {", 1)[1].split("}", 1)[0]

    assert "transform: none;" in image_stage_block
    assert "z-index: 2;" in image_stage_block
    assert "transform: rotate(-0.7deg);" in image_stage_card_block
    assert "background: #ffffff;" in image_stage_card_block
    assert "border: 1px solid rgba(18, 47, 91, 0.14);" in image_stage_card_block
    assert "radial-gradient" not in image_stage_card_block
    assert "linear-gradient" not in image_stage_card_block
    assert "inset -1px -1px 0 rgba(18, 47, 91, 0.07)" in image_stage_card_block
    assert "inset 1px 1px 0 rgba(255, 255, 255, 0.96)" in image_stage_card_block
    assert "transform: none;" in image_block
    assert "z-index: 1;" in image_block
    assert "inset " not in image_block
    assert "z-index: 0;" in panel_overlay_block


def test_main_optimized_assets_are_webp_and_small() -> None:
    from PIL import Image

    asset_dir = ROOT_DIR / "frontend" / "assets" / "main" / "optimized"
    asset_paths = [asset_dir / f"main-slide-{index:02d}.webp" for index in range(1, 6)]

    for asset_path in asset_paths:
        assert asset_path.exists()
        assert asset_path.stat().st_size <= 240_000
        with Image.open(asset_path) as image:
            assert image.format == "WEBP"
            assert max(image.size) <= 900
