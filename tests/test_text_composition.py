from io import BytesIO

from PIL import Image, ImageChops

from backend.app.core.config import Settings
from backend.app.core.presets import get_presets
from backend.app.core.text_layouts import TextLayout, find_text_layout, get_text_layouts
from backend.app.services.copywriting import AdCopy, build_ad_copy
from backend.app.services.text_overlay import render_text_overlay


def test_build_ad_copy_preserves_user_prompt_without_metadata() -> None:
    copy = build_ad_copy("광고 유형: 스토리 이미지\n오늘 아메리카노 2500원", "preserve")

    assert copy.headline == "오늘 아메리카노 2,500원"
    assert copy.subcopy is None
    assert copy.cta is None
    assert copy.mode == "preserve"


def test_build_ad_copy_polishes_user_prompt() -> None:
    copy = build_ad_copy("  오늘   라떼   4500원  ", "polish")

    assert copy.headline == "오늘 라떼 4,500원"
    assert copy.subcopy == "카페에서 더 맛있게 즐겨보세요."
    assert copy.cta is None
    assert copy.mode == "polish"


def test_build_ad_copy_rewrites_with_promotional_context() -> None:
    copy = build_ad_copy("딸기 케이크 6500원", "rewrite")

    assert "딸기 케이크 6,500원" in copy.headline
    assert copy.subcopy is not None
    assert copy.cta == "지금 방문해보세요"
    assert copy.mode == "rewrite"


def test_build_ad_copy_returns_fallback_when_user_prompt_is_empty() -> None:
    copy = build_ad_copy("광고 유형: 메뉴 이미지", "preserve")

    assert copy.headline
    assert copy.subcopy
    assert copy.cta
    assert copy.mode == "preserve"


def test_text_layouts_cover_all_preset_details() -> None:
    presets = get_presets()
    layouts = get_text_layouts()

    for preset in presets.values():
        assert preset.id in layouts
        for detail in preset.details:
            layout = find_text_layout(preset.id, detail.id)
            assert layout.safe_margin >= 0
            assert 0 < layout.max_width_ratio <= 1
            assert layout.max_lines >= 1


def test_render_text_overlay_draws_copy_on_image() -> None:
    source = Image.new("RGB", (640, 640), "white")
    source_output = BytesIO()
    source.save(source_output, format="PNG")
    source_bytes = source_output.getvalue()
    layout = TextLayout(
        position="top_left",
        safe_margin=48,
        max_width_ratio=0.7,
        headline_font_ratio=0.08,
        subcopy_font_ratio=0.04,
        cta_font_ratio=0.04,
        max_lines=3,
        align="left",
        color="#111111",
        shadow=False,
        backdrop=False,
    )
    ad_copy = AdCopy(
        headline="Coffee Sale",
        subcopy="Today only",
        cta="Visit now",
        mode="rewrite",
    )

    rendered_bytes = render_text_overlay(source_bytes, ad_copy, layout, Settings())

    with Image.open(BytesIO(rendered_bytes)) as rendered:
        assert rendered.size == (640, 640)
        diff = ImageChops.difference(source, rendered.convert("RGB"))
        assert diff.getbbox() is not None
