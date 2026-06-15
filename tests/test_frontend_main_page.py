import ast
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"
FRONTEND_MAIN_PAGE = ROOT_DIR / "frontend" / "pages" / "main.py"
FRONTEND_ROUTER = ROOT_DIR / "frontend" / "core" / "router.py"
STYLE_MAIN_LAYOUT_FILE = ROOT_DIR / "frontend" / "css" / "main_layout.py"
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
    assert 'href="?page=work"' in main_source
    assert 'target="_self"' in main_source
    assert 'st.session_state.get("current_page", "main")' not in app_source
    assert "사장님의 메뉴 사진을" in main_source
    assert "광고 이미지로 바꾸는" in main_source
    assert "무료로 시작하기" in main_source
    assert "landing-start-link" in main_source
    assert "landing-url-chip" not in main_source
    assert "go-gachi.ai/우리카페" not in main_source
    assert "landing-menu" not in main_source
    assert "서비스" not in main_source
    assert "템플릿" not in main_source
    assert "활용법" not in main_source
    assert "요금" not in main_source


def test_main_page_styles_match_linktree_inspired_hero() -> None:
    styles = STYLE_MAIN_LAYOUT_FILE.read_text(encoding="utf-8") + STYLE_MAIN_VISUAL_FILE.read_text(
        encoding="utf-8"
    )

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
