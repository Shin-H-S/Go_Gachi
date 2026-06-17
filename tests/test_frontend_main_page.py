import ast
import importlib
import re
from pathlib import Path
from types import SimpleNamespace

from frontend.css.main_layout import MAIN_LAYOUT_CSS

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"
FRONTEND_MAIN_PAGE = ROOT_DIR / "frontend" / "pages" / "main.py"
FRONTEND_ROUTER = ROOT_DIR / "frontend" / "core" / "router.py"
STYLE_MAIN_VISUAL_FILE = ROOT_DIR / "frontend" / "css" / "main_visual.py"


def test_main_page_module_exposes_route_and_copy() -> None:
    app_source = FRONTEND_APP.read_text(encoding="utf-8")
    main_source = FRONTEND_MAIN_PAGE.read_text(encoding="utf-8")
    router_source = FRONTEND_ROUTER.read_text(encoding="utf-8")
    tree = ast.parse(main_source)
    defined_functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    assert "render_main_page" in defined_functions
    assert "get_current_page" in router_source
    assert "st.query_params" in router_source
    assert 'href="?page=work"' not in main_source
    assert "main-start-button-marker" in main_source
    assert "main-start-button" in main_source
    assert 'target="_self"' in main_source
    assert 'st.session_state.get("current_page", "main")' not in app_source
    assert "사장님의 메뉴 사진을" in main_source
    assert "광고 이미지로 바꾸는" in main_source
    assert "무료로 시작하기" in main_source
    assert "landing-url-chip" not in main_source
    assert "go-gachi.ai/우리카페" not in main_source
    assert "landing-menu" not in main_source
    assert "서비스" not in main_source
    assert "템플릿" not in main_source
    assert "활용법" not in main_source
    assert "요금" not in main_source


def test_main_start_click_routes_by_auth_state(monkeypatch) -> None:
    main_page = importlib.import_module("frontend.pages.main")

    logged_out_navigation: list[str] = []
    logged_out_reruns: list[str] = []
    logged_out_st = SimpleNamespace(
        session_state={"auth_access_token": "", "auth_redirect_page": "login"},
        rerun=lambda: logged_out_reruns.append("rerun"),
    )
    monkeypatch.setattr(main_page, "st", logged_out_st)
    monkeypatch.setattr(main_page, "navigate_to", logged_out_navigation.append)

    main_page._handle_start_click()

    assert logged_out_navigation == ["work"]
    assert logged_out_st.session_state["auth_access_token"] == ""
    assert logged_out_st.session_state["auth_redirect_page"] == ""
    assert logged_out_reruns == ["rerun"]

    logged_in_navigation: list[str] = []
    logged_in_reruns: list[str] = []
    logged_in_st = SimpleNamespace(
        session_state={"auth_access_token": "token-123", "auth_redirect_page": "login"},
        rerun=lambda: logged_in_reruns.append("rerun"),
    )
    monkeypatch.setattr(main_page, "st", logged_in_st)
    monkeypatch.setattr(main_page, "navigate_to", logged_in_navigation.append)

    main_page._handle_start_click()

    assert logged_in_navigation == ["work"]
    assert logged_in_st.session_state["auth_access_token"] == "token-123"
    assert logged_in_st.session_state["auth_redirect_page"] == ""
    assert logged_in_reruns == ["rerun"]


def test_main_page_styles_match_linktree_inspired_hero() -> None:
    styles = MAIN_LAYOUT_CSS + STYLE_MAIN_VISUAL_FILE.read_text(encoding="utf-8")

    assert ".main-landing" in styles
    assert ".landing-nav" in styles
    assert ".hero-title" in styles
    assert ".blue-slide-track" in styles
    assert "@keyframes blue-panel-slide" in styles
    assert "#d8ff00" in styles
    assert ".landing-login {" in styles
    assert ".landing-signup {" in styles
    assert ".landing-login:hover" in styles
    assert ".landing-signup:hover" in styles
    assert "text-decoration: none !important;" in styles
    landing_block = styles.split(".st-key-main-landing {", 1)[1].split("}", 1)[0]
    assert "min-height: 100vh;" in landing_block
    assert "calc(100vh - 64px)" not in landing_block
    assert ".stApp:has(.st-key-main-landing)" in styles
    assert '[data-testid="stMain"]:has(.st-key-main-landing)' in styles
    assert ".landing-login {\n    background: #eff1ec;\n    color: #0b0e14 !important;" in styles
    assert (
        ".landing-signup {\n"
        "    border-radius: 999px;\n"
        "    background: #1e2433;\n"
        "    color: #ffffff !important;"
    ) in styles


def test_main_visual_html_uses_optimized_webp_slides(monkeypatch) -> None:
    main_page = importlib.import_module("frontend.pages.main")
    monkeypatch.setattr(main_page, "_main_slide_image_src", lambda filename: f"asset://{filename}")

    html = main_page._build_hero_visual_html()

    for index in range(1, 6):
        assert f"main-slide-{index:02d}.webp" in html
    assert html.count('<article class="blue-panel') == 6
    assert html.count('class="blue-panel-image"') == 6
    assert 'loading="eager"' in html
    assert 'loading="lazy"' in html


def test_main_visual_html_uses_korean_slide_captions(monkeypatch) -> None:
    main_page = importlib.import_module("frontend.pages.main")
    monkeypatch.setattr(main_page, "_main_slide_image_src", lambda filename: f"asset://{filename}")

    html = main_page._build_hero_visual_html()

    expected_pairs = (
        ("당근마켓", "메뉴 이미지"),
        ("인스타그램", "정사각형 피드"),
        ("당근마켓", "메뉴 이미지"),
        ("배달의 민족", "단색 배경 이미지"),
        ("인스타그램", "정사각형 피드"),
        ("당근마켓", "메뉴 이미지"),
    )
    assert tuple(re.findall(r"<span>(.*?)</span>\n<strong>(.*?)</strong>", html)) == expected_pairs
    for old_caption in (
        "동네 메뉴 홍보",
        "정사각형 피드 광고",
        "동네 홍보",
        "추천 메뉴 강조",
        "배달앱",
        "주문 배너",
        "SNS 피드",
        "바로 쓰는 광고",
        "Daangn Market",
        "Local menu card",
    ):
        assert old_caption not in html


def test_main_visual_html_does_not_render_as_markdown_code(monkeypatch) -> None:
    main_page = importlib.import_module("frontend.pages.main")
    monkeypatch.setattr(main_page, "_main_slide_image_src", lambda filename: f"asset://{filename}")

    html = main_page._build_hero_visual_html()

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


def test_main_start_button_keeps_original_cta_visual_contract() -> None:
    styles = MAIN_LAYOUT_CSS
    container_selector = ".st-key-main-start-button {"
    button_selector = ".st-key-main-start-button button {"
    button_base_selector = (
        '.st-key-main-start-button div[data-testid="stButton"] '
        'button[data-testid="stBaseButton-secondary"] {'
    )
    button_text_selector = (
        '.st-key-main-start-button div[data-testid="stButton"]\n'
        '    button[data-testid="stBaseButton-secondary"] * {'
    )

    assert container_selector in styles
    assert button_selector in styles
    assert button_text_selector in styles
    assert button_base_selector in styles
    container_block = styles.split(container_selector, 1)[1].split("}", 1)[0]
    button_block = styles.split(button_selector, 1)[1].split("}", 1)[0]
    button_text_block = styles.split(button_text_selector, 1)[1].split("}", 1)[0]

    assert "width: min(380px, 100%) !important;" in container_block
    assert "display: flex !important;" in button_block
    assert "align-items: center !important;" in button_block
    assert "justify-content: center !important;" in button_block
    assert "min-height: 80px !important;" in button_block
    assert "width: 100% !important;" in button_block
    assert "border-radius: 999px !important;" in button_block
    assert "background: #24551e !important;" in button_block
    assert "background-color: #24551e !important;" in button_block
    assert "background-image: none !important;" in button_block
    assert "font-size: 27.3px !important;" in button_block
    assert "font-weight: 950 !important;" in button_block
    assert "color: #ffffff !important;" in button_block
    assert "-webkit-text-fill-color: #ffffff !important;" in button_block
    assert "box-shadow: 0 18px 34px rgba(36, 85, 30, 0.28) !important;" in button_block
    assert "box-sizing: border-box !important;" in button_block
    assert "color: #ffffff !important;" in button_text_block
    assert "-webkit-text-fill-color: #ffffff !important;" in button_text_block
    assert "font-size: 27.3px !important;" in button_text_block
