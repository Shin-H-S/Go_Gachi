import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"
FRONTEND_MAIN_PAGE = ROOT_DIR / "frontend" / "pages" / "main.py"
FRONTEND_MAIN_NAVIGATION = ROOT_DIR / "frontend" / "main" / "navigation.py"
FRONTEND_ROUTER = ROOT_DIR / "frontend" / "core" / "router.py"


def test_main_page_module_exposes_route_and_copy() -> None:
    app_source = FRONTEND_APP.read_text(encoding="utf-8")
    main_source = FRONTEND_MAIN_PAGE.read_text(encoding="utf-8")
    nav_source = FRONTEND_MAIN_NAVIGATION.read_text(encoding="utf-8")
    router_source = FRONTEND_ROUTER.read_text(encoding="utf-8")
    tree = ast.parse(main_source)
    defined_functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    combined_source = main_source + nav_source

    assert "render_main_page" in defined_functions
    assert "get_current_page" in router_source
    assert "st.query_params" in router_source
    assert 'href="?page=work"' not in combined_source
    assert "main-start-button-marker" in main_source
    assert "main-start-button" in main_source
    assert 'target="_self"' in nav_source
    assert 'st.session_state.get("current_page", "main")' not in app_source
    assert "AI CAFE AD MAKER" in main_source
    assert "hero-title" in main_source
    assert "hero-copy" in main_source
    assert "landing-url-chip" not in combined_source
    assert "go-gachi.ai/" not in combined_source
    assert "landing-menu" not in combined_source
    assert "landing-menu" not in combined_source


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
