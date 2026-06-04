import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"
FRONTEND_ROUTER = ROOT_DIR / "frontend" / "core" / "router.py"
FRONTEND_LOGIN_PAGE = ROOT_DIR / "frontend" / "pages" / "login.py"
FRONTEND_LOGIN_CSS = ROOT_DIR / "frontend" / "css" / "login.py"
FRONTEND_AUTH_SESSION = ROOT_DIR / "frontend" / "auth" / "session.py"
FRONTEND_STYLES = ROOT_DIR / "frontend" / "styles.py"


def read_source(path: Path) -> str:
    assert path.exists(), f"{path.relative_to(ROOT_DIR)} should exist"
    return path.read_text(encoding="utf-8")


def test_login_route_is_registered_and_dispatched() -> None:
    app_source = read_source(FRONTEND_APP)
    router_source = read_source(FRONTEND_ROUTER)

    assert '"login"' in router_source
    assert 'router.navigate_to("login")' not in app_source
    assert "from frontend.pages.login import render_login_page" in app_source
    assert 'current_page == "login"' in app_source
    assert "render_login_page()" in app_source


def test_login_page_has_email_password_only_copy_and_english_brand() -> None:
    source = read_source(FRONTEND_LOGIN_PAGE)
    tree = ast.parse(source)
    defined_functions = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }

    assert "render_login_page" in defined_functions
    assert "이메일" in source
    assert "비밀번호" in source
    assert "로그인" in source
    assert "Go Gachi" in source
    assert "고가치" not in source
    assert "다시 로그인해주세요" in source
    assert "회원가입" in source
    assert "sign_in_with_password" not in source
    assert "/api/login" not in source
    assert "/api/signup" not in source

    social_words = ["Google", "Apple", "구글", "카카오", "네이버", "소셜", "Continue with"]
    assert all(word not in source for word in social_words)


def test_login_styles_use_solid_blue_right_panel_without_images() -> None:
    styles = read_source(FRONTEND_LOGIN_CSS)
    composed_styles = read_source(FRONTEND_STYLES)

    assert "LOGIN_CSS" in styles
    assert ".login-blue-panel" in styles
    assert "#2563c7" in styles
    assert "background-image" not in styles
    assert "url(" not in styles
    assert "from frontend.css.login import LOGIN_CSS" in composed_styles


def test_email_login_helper_returns_token_session() -> None:
    read_source(FRONTEND_AUTH_SESSION)
    auth_session = importlib.import_module("frontend.auth.session")

    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_in_with_password=lambda payload: SimpleNamespace(
                session=SimpleNamespace(access_token="token-123"),
                user=SimpleNamespace(id="user-123", email=payload["email"]),
            )
        )
    )

    session = auth_session.login_with_email(
        "  owner@example.com  ",
        "password123",
        supabase_client=fake_client,
    )

    assert session.access_token == "token-123"
    assert session.user_id == "user-123"
    assert session.email == "owner@example.com"


def test_email_login_helper_rejects_missing_supabase_session() -> None:
    read_source(FRONTEND_AUTH_SESSION)
    auth_session = importlib.import_module("frontend.auth.session")
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_in_with_password=lambda _payload: SimpleNamespace(session=None, user=None)
        )
    )

    with pytest.raises(auth_session.AuthLoginError, match="로그인 세션"):
        auth_session.login_with_email(
            "owner@example.com",
            "password123",
            supabase_client=fake_client,
        )


def test_auth_session_state_defaults_and_save(monkeypatch) -> None:
    read_source(FRONTEND_AUTH_SESSION)
    router = importlib.import_module("frontend.core.router")
    auth_session = importlib.import_module("frontend.auth.session")
    fake_st = SimpleNamespace(session_state={})
    monkeypatch.setattr(router, "st", fake_st)

    router.init_session_state()

    assert fake_st.session_state["is_logged_in"] is False
    assert fake_st.session_state["auth_access_token"] == ""
    assert fake_st.session_state["auth_user_email"] == ""

    auth_session.save_auth_session(
        fake_st.session_state,
        auth_session.EmailAuthSession(
            access_token="token-123",
            user_id="user-123",
            email="owner@example.com",
        ),
    )

    assert fake_st.session_state["is_logged_in"] is True
    assert fake_st.session_state["auth_access_token"] == "token-123"
    assert fake_st.session_state["auth_user_id"] == "user-123"
    assert fake_st.session_state["auth_user_email"] == "owner@example.com"
