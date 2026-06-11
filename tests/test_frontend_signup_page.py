import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"
FRONTEND_ROUTER = ROOT_DIR / "frontend" / "core" / "router.py"
FRONTEND_SIGNUP_PAGE = ROOT_DIR / "frontend" / "pages" / "signup.py"
FRONTEND_SIGNUP_CSS = ROOT_DIR / "frontend" / "css" / "signup.py"
FRONTEND_AUTH_SESSION = ROOT_DIR / "frontend" / "auth" / "session.py"
FRONTEND_STYLES = ROOT_DIR / "frontend" / "styles.py"


def read_source(path: Path) -> str:
    assert path.exists(), f"{path.relative_to(ROOT_DIR)} should exist"
    return path.read_text(encoding="utf-8")


def test_signup_route_is_registered_and_dispatched() -> None:
    app_source = read_source(FRONTEND_APP)
    router_source = read_source(FRONTEND_ROUTER)

    assert '"signup"' in router_source
    assert "from frontend.pages.signup import render_signup_page" in app_source
    assert 'current_page == "signup"' in app_source
    assert "render_signup_page()" in app_source


def test_signup_page_collects_contract_fields_without_social_login_or_backend_signup() -> None:
    source = read_source(FRONTEND_SIGNUP_PAGE)
    tree = ast.parse(source)
    defined_functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    assert "render_signup_page" in defined_functions
    assert "Go Gachi" in source
    assert "회원가입" in source
    assert "이메일" in source
    assert "비밀번호" in source
    assert "닉네임" in source
    assert "표시 이름" not in source
    assert "표시할 이름" not in source
    assert "계정 만들기" in source
    assert "로그인" in source
    assert "sign_up" not in source
    assert "/api/login" not in source
    assert "/api/signup" not in source

    social_words = ["Google", "Apple", "구글", "카카오", "네이버", "소셜", "Continue with"]
    assert all(word not in source for word in social_words)


def test_signup_styles_use_solid_blue_right_panel_without_images() -> None:
    styles = read_source(FRONTEND_SIGNUP_CSS)
    composed_styles = read_source(FRONTEND_STYLES)

    assert "SIGNUP_CSS" in styles
    assert ".signup-blue-panel" in styles
    assert "#2563c7" in styles
    assert "background-image" not in styles
    assert "url(" not in styles
    assert "from frontend.css.signup import SIGNUP_CSS" in composed_styles


def test_signup_helper_sends_display_name_metadata_and_does_not_require_session() -> None:
    read_source(FRONTEND_AUTH_SESSION)
    auth_session = importlib.import_module("frontend.auth.session")
    captured = {}

    def fake_sign_up(payload):
        captured.update(payload)
        return SimpleNamespace(
            session=None,
            user=SimpleNamespace(id="user-123", email=payload["email"]),
        )

    fake_client = SimpleNamespace(auth=SimpleNamespace(sign_up=fake_sign_up))

    result = auth_session.signup_with_email(
        "  owner@example.com  ",
        "password123",
        "  카페 사장님  ",
        supabase_client=fake_client,
    )

    assert captured == {
        "email": "owner@example.com",
        "password": "password123",
        "options": {"data": {"display_name": "카페 사장님"}},
    }
    assert result.user_id == "user-123"
    assert result.email == "owner@example.com"
    assert result.display_name == "카페 사장님"


def test_signup_helper_validates_required_contract_fields() -> None:
    read_source(FRONTEND_AUTH_SESSION)
    auth_session = importlib.import_module("frontend.auth.session")

    with pytest.raises(auth_session.AuthSignupError, match="닉네임"):
        auth_session.signup_with_email("owner@example.com", "password123", "   ")

    with pytest.raises(auth_session.AuthSignupError, match="8자"):
        auth_session.signup_with_email("owner@example.com", "short", "카페 사장님")
