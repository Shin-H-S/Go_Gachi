import ast
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"
FRONTEND_MYPAGE_PAGE = ROOT_DIR / "frontend" / "pages" / "mypage.py"
FRONTEND_ROUTER = ROOT_DIR / "frontend" / "core" / "router.py"
FRONTEND_API_CLIENT = ROOT_DIR / "frontend" / "services" / "api_client.py"
FRONTEND_MYPAGE_CARD = ROOT_DIR / "frontend" / "mypage" / "generation_card.py"
FRONTEND_MYPAGE_SIDEBAR = ROOT_DIR / "frontend" / "mypage" / "sidebar.py"
FRONTEND_STYLES = ROOT_DIR / "frontend" / "styles.py"
STYLE_MYPAGE_FILE = ROOT_DIR / "frontend" / "css" / "mypage.py"
STYLE_MYPAGE_LAYOUT = ROOT_DIR / "frontend" / "css" / "mypage_parts" / "layout.py"
STYLE_MYPAGE_CARDS = ROOT_DIR / "frontend" / "css" / "mypage_parts" / "cards.py"
STYLE_MYPAGE_NAVIGATION = ROOT_DIR / "frontend" / "css" / "mypage_parts" / "navigation.py"


def test_mypage_page_is_routed_and_split_into_focused_renderers() -> None:
    app_source = FRONTEND_APP.read_text(encoding="utf-8")
    router_source = FRONTEND_ROUTER.read_text(encoding="utf-8")
    page_source = FRONTEND_MYPAGE_PAGE.read_text(encoding="utf-8")
    tree = ast.parse(page_source)
    defined_functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    assert '"mypage"' in router_source
    assert "render_mypage_page" in app_source
    assert 'current_page == "mypage"' in app_source
    assert {
        "render_mypage_page",
        "render_recent_work",
        "render_folder_view",
        "render_uploads",
        "render_account_settings",
    }.issubset(defined_functions)
    assert "닉네임의 마이페이지" in page_source
    assert "업로드한 메뉴 사진" in page_source
    assert "계정 설정" in page_source
    assert "새 폴더" in page_source
    assert "새로 생성하기" in page_source


def test_app_does_not_import_mypage_until_route_is_selected() -> None:
    tree = ast.parse(FRONTEND_APP.read_text(encoding="utf-8"))
    top_level_imports = [
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    ]

    assert "frontend.pages.mypage" not in top_level_imports


def test_mypage_api_and_styles_are_registered() -> None:
    api_source = FRONTEND_API_CLIENT.read_text(encoding="utf-8")
    styles_source = FRONTEND_STYLES.read_text(encoding="utf-8")
    mypage_composer = STYLE_MYPAGE_FILE.read_text(encoding="utf-8")
    layout_styles = STYLE_MYPAGE_LAYOUT.read_text(encoding="utf-8")
    card_styles = STYLE_MYPAGE_CARDS.read_text(encoding="utf-8")

    assert "request_my_generations" in api_source
    assert "request_my_folders" in api_source
    assert "request_my_uploads" in api_source
    assert "create_my_folder" in api_source
    assert "move_generation_to_folder" in api_source
    assert "MYPAGE_CSS" in styles_source
    assert "MYPAGE_LAYOUT_CSS" in mypage_composer
    assert ".mypage-shell" in layout_styles
    assert ".mypage-card-grid" in card_styles


def test_generation_folder_select_assigns_without_extra_button() -> None:
    source = FRONTEND_MYPAGE_CARD.read_text(encoding="utf-8")

    assert "mypage-move-" not in source
    assert "on_change=_assign_generation_folder" in source
    assert "move_generation_to_folder" in source


def test_generation_download_uses_streamlit_download_button() -> None:
    source = FRONTEND_MYPAGE_CARD.read_text(encoding="utf-8")

    assert 'target="_blank">다운로드</a>' not in source
    assert "st.download_button(" in source
    assert "request_asset_bytes" in source


def test_new_folder_action_lives_under_sidebar_all_button() -> None:
    source = FRONTEND_MYPAGE_SIDEBAR.read_text(encoding="utf-8")
    compact_source = "".join(source.split())
    navigation_styles = STYLE_MYPAGE_NAVIGATION.read_text(encoding="utf-8")

    all_button_index = source.index('key="mypage-folder-all"')
    new_folder_index = source.index('"새 폴더 만들기"')

    assert all_button_index < new_folder_index
    assert "new_folder_col" not in source
    assert '="mypage_show_folder_form"' not in compact_source
    assert '=notst.session_state.get("mypage_show_folder_form",False,)' in compact_source
    assert ".st-key-mypage-new-folder button::before" in navigation_styles
    assert 'content: "+"' in navigation_styles
    assert (
        "render_sidebar(profile: dict, folders: list[dict], view: str, access_token: str)"
        in source
    )
