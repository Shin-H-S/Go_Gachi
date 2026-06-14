import ast
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"
FRONTEND_MYPAGE_PAGE = ROOT_DIR / "frontend" / "pages" / "mypage.py"
FRONTEND_ROUTER = ROOT_DIR / "frontend" / "core" / "router.py"
FRONTEND_API_CLIENT = ROOT_DIR / "frontend" / "services" / "api_client.py"
FRONTEND_MYPAGE_CARD = ROOT_DIR / "frontend" / "mypage" / "generation_card.py"
FRONTEND_MYPAGE_SECTIONS = ROOT_DIR / "frontend" / "mypage" / "page_sections.py"
FRONTEND_MYPAGE_VIEWS = ROOT_DIR / "frontend" / "mypage" / "views.py"
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
    sections_source = FRONTEND_MYPAGE_SECTIONS.read_text(encoding="utf-8")
    page_tree = ast.parse(page_source)
    sections_tree = ast.parse(sections_source)
    page_functions = {
        node.name for node in ast.walk(page_tree) if isinstance(node, ast.FunctionDef)
    }
    section_functions = {
        node.name for node in ast.walk(sections_tree) if isinstance(node, ast.FunctionDef)
    }

    assert '"mypage"' in router_source
    assert "render_mypage_page" in app_source
    assert 'current_page == "mypage"' in app_source
    assert "render_mypage_page" in page_functions
    assert {
        "render_recent_work",
        "render_folder_view",
        "render_uploads",
        "render_account_settings",
    }.issubset(section_functions)
    assert "닉네임의 마이페이지" in page_source
    assert "업로드한 메뉴 사진" in page_source
    assert "계정 설정" in page_source
    assert "전체 작업" in page_source
    assert "새 폴더" in page_source
    assert "새로 생성하기" in page_source


def test_mypage_login_prompt_sets_return_route_before_login() -> None:
    page_source = FRONTEND_MYPAGE_PAGE.read_text(encoding="utf-8")

    assert '"auth_redirect_page"' in page_source
    assert '"mypage"' in page_source
    assert 'navigate_to("login")' in page_source


def test_app_does_not_import_mypage_until_route_is_selected() -> None:
    tree = ast.parse(FRONTEND_APP.read_text(encoding="utf-8"))
    top_level_imports = [node.module for node in tree.body if isinstance(node, ast.ImportFrom)]

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


def test_mypage_generations_api_accepts_page_query() -> None:
    api_source = FRONTEND_API_CLIENT.read_text(encoding="utf-8")

    assert "def request_my_generations(access_token: str, page: int = 1)" in api_source
    assert 'f"/api/auth/me/generations?page={page}"' in api_source


def test_mypage_loads_generation_pages_and_uses_total_count() -> None:
    page_source = FRONTEND_MYPAGE_PAGE.read_text(encoding="utf-8")

    assert "def _load_generation_pages(access_token: str)" in page_source
    assert "total_count" in page_source
    assert "request_my_generations(access_token, page=page)" in page_source


def test_mypage_views_render_collection_status_and_pagination() -> None:
    views_source = FRONTEND_MYPAGE_VIEWS.read_text(encoding="utf-8")

    assert "render_pagination_controls(" in views_source
    assert "page_status_text(" in views_source
    assert "mypage-list-status" in views_source


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


def test_sidebar_removes_duplicate_all_folder_action() -> None:
    source = FRONTEND_MYPAGE_SIDEBAR.read_text(encoding="utf-8")
    compact_source = "".join(source.split())
    navigation_styles = STYLE_MYPAGE_NAVIGATION.read_text(encoding="utf-8")

    new_folder_index = source.index('"새 폴더 만들기"')
    account_index = source.index('"계정 설정"')
    uncategorized_index = source.index('key="mypage-folder-none"')

    assert 'key="mypage-folder-all"' not in source
    assert "FOLDER_ALL_VIEW" not in source
    assert ".st-key-mypage-folder-all" not in navigation_styles
    assert "mypage-current-view" not in source
    assert ".mypage-current-view" not in navigation_styles
    assert "view_title" not in source
    assert uncategorized_index < account_index < new_folder_index
    assert "new_folder_col" not in source
    assert '="mypage_show_folder_form"' not in compact_source
    assert '=notst.session_state.get("mypage_show_folder_form",False,)' in compact_source
    assert '"+ 새 폴더 만들기"' not in source
    assert ".st-key-mypage-new-folder button::before" in navigation_styles
    assert "justify-content: center !important" in navigation_styles
    assert "justify-content: flex-start !important" not in navigation_styles
    new_folder_label_selector = (
        '.st-key-mypage-new-folder button div[data-testid="stMarkdownContainer"]'
    )
    assert new_folder_label_selector in navigation_styles
    assert ".st-key-mypage-new-folder button p" in navigation_styles
    assert "flex: 0 0 auto !important" in navigation_styles
    assert "width: auto !important" in navigation_styles
    assert "gap: 8px !important" in navigation_styles
    assert "margin-right: 0" in navigation_styles
    assert 'content: "+"' in navigation_styles
    assert (
        "render_sidebar(profile: dict, folders: list[dict], view: str, access_token: str)" in source
    )
