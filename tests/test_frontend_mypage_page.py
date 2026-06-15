import ast
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"
FRONTEND_MYPAGE_PAGE = ROOT_DIR / "frontend" / "pages" / "mypage.py"
FRONTEND_ROUTER = ROOT_DIR / "frontend" / "core" / "router.py"
FRONTEND_API_CLIENT = ROOT_DIR / "frontend" / "services" / "api_client.py"
FRONTEND_MYPAGE_CARD = ROOT_DIR / "frontend" / "mypage" / "generation_card.py"
FRONTEND_MYPAGE_SECTIONS = ROOT_DIR / "frontend" / "mypage" / "page_sections.py"
FRONTEND_MYPAGE_STATE = ROOT_DIR / "frontend" / "mypage" / "state.py"
FRONTEND_MYPAGE_TOPBAR = ROOT_DIR / "frontend" / "mypage" / "topbar.py"
FRONTEND_MYPAGE_VIEWS = ROOT_DIR / "frontend" / "mypage" / "views.py"
FRONTEND_MYPAGE_SIDEBAR = ROOT_DIR / "frontend" / "mypage" / "sidebar.py"
FRONTEND_STYLES = ROOT_DIR / "frontend" / "styles.py"
STYLE_MYPAGE_FILE = ROOT_DIR / "frontend" / "css" / "mypage.py"
STYLE_MYPAGE_LAYOUT = ROOT_DIR / "frontend" / "css" / "mypage_parts" / "layout.py"
STYLE_MYPAGE_CARDS = ROOT_DIR / "frontend" / "css" / "mypage_parts" / "cards.py"
STYLE_MYPAGE_NAVIGATION = ROOT_DIR / "frontend" / "css" / "mypage_parts" / "navigation.py"
STYLE_MYPAGE_NAVIGATION_ACTIONS = (
    ROOT_DIR / "frontend" / "css" / "mypage_parts" / "navigation_actions.py"
)


def _read_mypage_navigation_styles() -> str:
    return "\n".join(
        (
            STYLE_MYPAGE_NAVIGATION.read_text(encoding="utf-8"),
            STYLE_MYPAGE_NAVIGATION_ACTIONS.read_text(encoding="utf-8"),
        )
    )


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
    assert "업로드한 원본 이미지" in page_source
    assert "계정 설정" in page_source
    assert "전체 작업" in page_source
    assert "새 폴더" in page_source
    assert "작업 페이지로 돌아가기" in page_source


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
    page_source = FRONTEND_MYPAGE_PAGE.read_text(encoding="utf-8")
    layout_styles = STYLE_MYPAGE_LAYOUT.read_text(encoding="utf-8")
    card_styles = STYLE_MYPAGE_CARDS.read_text(encoding="utf-8")
    navigation_styles = _read_mypage_navigation_styles()
    sidebar_source = FRONTEND_MYPAGE_SIDEBAR.read_text(encoding="utf-8")
    new_work_button_block = navigation_styles.split(
        ".st-key-mypage-new-work button,",
        1,
    )[1].split("}", 1)[0]
    new_work_not_hover_block = navigation_styles.split(
        ".st-key-mypage-new-work button:not(:hover),",
        1,
    )[1].split("}", 1)[0]
    sidebar_column_block = layout_styles.split(
        '.st-key-mypage-shell [data-testid="column"]:has(.mypage-sidebar-head)',
        1,
    )[1].split("}", 1)[0]
    sidebar_button_block = navigation_styles.split(
        '.st-key-mypage-shell [data-testid="column"]:has(.mypage-sidebar-head) button',
        1,
    )[1].split("}", 1)[0]
    sidebar_nav_button_block = navigation_styles.split(
        ".st-key-mypage-nav-recent button,",
        1,
    )[1].split("}", 1)[0]

    assert "request_my_generations" in api_source
    assert "request_my_folders" in api_source
    assert "request_my_uploads" in api_source
    assert "create_my_folder" in api_source
    assert "move_generation_to_folder" in api_source
    assert "MYPAGE_CSS" in styles_source
    assert "MYPAGE_LAYOUT_CSS" in mypage_composer
    assert 'st.columns([0.176, 0.824], gap="large")' in page_source
    assert 'st.container(key="mypage-sidebar")' not in page_source
    assert ".mypage-shell" in layout_styles
    assert ".st-key-mypage-sidebar" not in layout_styles
    assert ".st-key-mypage-sidebar" not in navigation_styles
    assert "min-height" not in sidebar_column_block
    assert ".main .block-container:has(.st-key-mypage-shell)" in layout_styles
    assert "padding-top: 12px" in layout_styles
    assert '[data-testid="column"]:has(.mypage-sidebar-head)' in layout_styles
    assert "background: #ffffff !important" in sidebar_column_block
    assert ".st-key-mypage-new-work" in navigation_styles
    assert "font-size: 19.2px !important" in sidebar_button_block
    assert "border: 0 !important" in sidebar_button_block
    assert "border-width: 0 !important" in navigation_styles
    assert "border-color: transparent !important" in sidebar_button_block
    assert "outline: 0 !important" in navigation_styles
    assert "box-shadow: none !important" in sidebar_button_block
    assert "background: #ffffff !important" in sidebar_button_block
    assert "background-color: #ffffff !important" in sidebar_button_block
    assert "background: #ffffff !important" in sidebar_nav_button_block
    assert "background-color: #ffffff !important" in sidebar_nav_button_block
    assert "background: transparent !important" not in sidebar_nav_button_block
    assert "box-shadow: none !important" in sidebar_nav_button_block
    assert "mypage-sidebar-button-marker" in sidebar_source
    assert 'div[data-testid="stElementContainer"]:has(.mypage-sidebar-button-marker)' in (
        navigation_styles
    )
    assert '+ div[data-testid="stButton"]' in navigation_styles
    assert '+ div[data-testid="stFormSubmitButton"]' in navigation_styles
    assert "button::before" in navigation_styles
    assert "button::after" in navigation_styles
    assert "border: 1px solid rgba(24, 33, 31, 0.18)" not in navigation_styles
    assert "width: 60% !important" in new_work_button_block
    assert "border-radius: 999px !important" in new_work_button_block
    assert "background: #173d14 !important" in new_work_button_block
    assert "background-color: #173d14 !important" in new_work_button_block
    assert "background: #173d14 !important" in new_work_not_hover_block
    assert "background-color: #173d14 !important" in new_work_not_hover_block
    assert "min-height: 56px !important" in new_work_button_block
    assert "display: flex !important" in new_work_button_block
    assert "justify-content: center !important" in new_work_button_block
    assert "margin-left: auto" in new_work_button_block
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


def test_mypage_uses_requested_user_facing_copy() -> None:
    combined_source = "\n".join(
        [
            FRONTEND_MYPAGE_PAGE.read_text(encoding="utf-8"),
            FRONTEND_MYPAGE_STATE.read_text(encoding="utf-8"),
            FRONTEND_MYPAGE_TOPBAR.read_text(encoding="utf-8"),
            FRONTEND_MYPAGE_VIEWS.read_text(encoding="utf-8"),
            FRONTEND_MYPAGE_SIDEBAR.read_text(encoding="utf-8"),
            FRONTEND_MYPAGE_CARD.read_text(encoding="utf-8"),
        ]
    )

    assert "업로드한 원본 이미지" in combined_source
    assert "← 작업 페이지로 돌아가기" in combined_source
    assert "업로드한 메뉴 사진" not in combined_source
    assert "새로 생성하기" not in combined_source


def test_generation_folder_select_assigns_without_extra_button() -> None:
    source = FRONTEND_MYPAGE_CARD.read_text(encoding="utf-8")

    assert "mypage-move-" not in source
    assert "on_change=_assign_generation_folder" in source
    assert "move_generation_to_folder" in source


def test_generation_download_uses_link_button_with_signed_url() -> None:
    source = FRONTEND_MYPAGE_CARD.read_text(encoding="utf-8")

    assert 'target="_blank">다운로드</a>' not in source
    # signed download_url을 link_button으로 1클릭에 사용하므로 bytes 사전 fetch는 없다.
    assert "st.link_button(" in source
    assert "request_asset_bytes" not in source
    assert "st.download_button(" not in source


def test_sidebar_removes_duplicate_all_folder_action() -> None:
    source = FRONTEND_MYPAGE_SIDEBAR.read_text(encoding="utf-8")
    compact_source = "".join(source.split())
    navigation_styles = _read_mypage_navigation_styles()

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
