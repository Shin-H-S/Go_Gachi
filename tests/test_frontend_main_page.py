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


def test_main_page_renders_readable_korean_copy_and_line_breaks(monkeypatch) -> None:
    main_page = importlib.import_module("frontend.pages.main")
    fake_st = FakeMainPageStreamlit()

    monkeypatch.setattr(main_page, "st", fake_st)
    monkeypatch.setattr(main_page, "render_main_navigation", lambda: None)
    monkeypatch.setattr(main_page, "build_hero_visual_html", lambda: "<section></section>")

    main_page.render_main_page()

    rendered_html = "\n".join(fake_st.markdowns)
    assert "\uc0ac\uc7a5\ub2d8\uc758 \uba54\ub274 \uc0ac\uc9c4\uc744<br />" in rendered_html
    assert "\uad11\uace0 \uc774\ubbf8\uc9c0\ub85c \ubc14\uafb8\ub294<br />" in rendered_html
    assert "\uac00\uc7a5 \ube60\ub978 \ubc29\ubc95" in rendered_html
    assert "\ubb34\ub8cc\ub85c \uc2dc\uc791\ud558\uae30" in [
        button["label"] for button in fake_st.buttons
    ]
    assert "??br />" not in rendered_html
    assert "\u003c/a>" not in rendered_html


class FakeMainPageContext:
    def __enter__(self) -> "FakeMainPageContext":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


class FakeMainPageContainer:
    def __enter__(self) -> "FakeMainPageContainer":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


class FakeMainPageStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.markdowns: list[str] = []
        self.buttons: list[dict[str, object]] = []

    def container(self, *, key: str | None = None) -> FakeMainPageContainer:
        return FakeMainPageContainer()

    def columns(
        self,
        spec: object,
        *,
        gap: str | None = None,
        vertical_alignment: str | None = None,
    ) -> list[FakeMainPageContext]:
        count = len(spec) if isinstance(spec, list) else int(spec)
        return [FakeMainPageContext() for _ in range(count)]

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append(body)

    def button(self, label: str, **kwargs) -> bool:
        self.buttons.append({"label": label, **kwargs})
        return False
