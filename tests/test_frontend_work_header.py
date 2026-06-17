import importlib
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
WORK_HEADER = ROOT_DIR / "frontend" / "work" / "header.py"


def test_mypage_navigation_keeps_streamlit_session() -> None:
    source = WORK_HEADER.read_text(encoding="utf-8")

    assert 'href="?page=mypage"' not in source
    assert 'navigate_to("mypage")' in source
    assert 'key="work-mypage-link"' in source


def test_work_header_uses_dedicated_hero_container() -> None:
    source = WORK_HEADER.read_text(encoding="utf-8")

    assert 'st.container(key="work-hero")' in source


def test_work_header_renders_left_mypage_and_right_download_button() -> None:
    source = WORK_HEADER.read_text(encoding="utf-8")

    assert "[0.22, 0.60, 0.18]" in source
    assert "_render_mypage_profile_button()" in source
    assert "_render_work_auth_links()" in source
    assert "_render_home_button()" in source
    assert "_render_header_download_button()" in source
    assert "work-main-link" in source
    assert 'key="work-header-download-link"' in source
    assert 'key="work-header-download-button"' in source
    assert 'key="work-header-download-link"' in source
    assert 'key="work-header-download-fetch"' in source
    assert 'key="work-header-download-empty"' in source
    assert "GO-GACHI CAFE AD MAKER V1" not in source
    assert "brand-kicker" not in source
    assert "topbar" not in source
    assert "<h1" not in source


def test_work_header_profile_markup_is_not_rendered_as_code_block() -> None:
    source = WORK_HEADER.read_text(encoding="utf-8")

    assert "profile_html = (" in source
    assert "st.markdown(profile_html" in source
    assert '<div class="work-profile-card" aria-hidden="true">\n            <div' not in source


def test_work_header_profile_summary_uses_nickname_email_and_avatar() -> None:
    components = importlib.import_module("frontend.work.header")

    summary = components._build_mypage_profile_summary(
        {"display_name": " 송송 ", "email": "manatoki74@gmail.com"},
        is_logged_in=True,
    )

    assert summary == {
        "avatar": "송",
        "title": "송송의 마이페이지",
        "email": "manatoki74@gmail.com",
    }


def test_work_header_profile_summary_for_guest_has_question_mark_and_no_email() -> None:
    components = importlib.import_module("frontend.work.header")

    summary = components._build_mypage_profile_summary({}, is_logged_in=False)

    assert summary == {"avatar": "?", "title": "마이페이지", "email": ""}


def test_work_header_guest_renders_login_signup_links_instead_of_mypage(monkeypatch) -> None:
    components = importlib.import_module("frontend.work.header")
    fake_st = FakeHeaderStreamlit()
    navigated_pages: list[str] = []

    monkeypatch.setattr(components, "st", fake_st)
    monkeypatch.setattr(components, "navigate_to", navigated_pages.append)

    components.render_header()

    rendered_html = "\n".join(fake_st.markdowns)
    assert '<nav class="work-auth"' in rendered_html
    assert 'class="landing-login work-auth-login"' in rendered_html
    assert 'class="landing-signup work-auth-signup"' in rendered_html
    assert 'href="?page=login"' in rendered_html
    assert 'href="?page=signup"' in rendered_html
    assert "work-profile-card" not in rendered_html
    assert not any(button.get("key") == "work-mypage-link" for button in fake_st.buttons)
    assert any(button.get("key") == "work-main-link" for button in fake_st.buttons)
    assert navigated_pages == []


def test_work_header_logged_in_renders_mypage_instead_of_guest_auth(monkeypatch) -> None:
    components = importlib.import_module("frontend.work.header")
    fake_st = FakeHeaderStreamlit()
    fake_st.session_state["auth_access_token"] = "jwt-token"
    fake_st.session_state["auth_user_email"] = "owner@example.com"
    fake_st.session_state[components.WORK_HEADER_PROFILE_TOKEN_KEY] = "jwt-token"
    fake_st.session_state[components.WORK_HEADER_PROFILE_KEY] = {
        "display_name": "Owner",
        "email": "owner@example.com",
    }
    navigated_pages: list[str] = []

    monkeypatch.setattr(components, "st", fake_st)
    monkeypatch.setattr(components, "navigate_to", navigated_pages.append)

    components.render_header()

    rendered_html = "\n".join(fake_st.markdowns)
    assert "work-profile-card" in rendered_html
    assert '<nav class="work-auth"' not in rendered_html
    assert 'href="?page=login"' not in rendered_html
    assert 'href="?page=signup"' not in rendered_html
    assert any(button.get("key") == "work-mypage-link" for button in fake_st.buttons)
    assert any(button.get("key") == "work-main-link" for button in fake_st.buttons)
    assert navigated_pages == []


class FakeHeaderContext:
    def __enter__(self) -> "FakeHeaderContext":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


class FakeHeaderContainer:
    def __init__(self, fake_st: "FakeHeaderStreamlit") -> None:
        self.fake_st = fake_st

    def __enter__(self) -> "FakeHeaderContainer":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def columns(
        self,
        spec: object,
        *,
        gap: str | None = None,
        vertical_alignment: str | None = None,
    ) -> list[FakeHeaderContext]:
        self.fake_st.columns_calls.append((spec, gap, vertical_alignment))
        count = len(spec) if isinstance(spec, list) else int(spec)
        return [FakeHeaderContext() for _ in range(count)]


class FakeHeaderStreamlit:
    def __init__(self, clicked_key: str | None = None) -> None:
        self.session_state: dict[str, object] = {}
        self.clicked_key = clicked_key
        self.markdowns: list[str] = []
        self.buttons: list[dict[str, object]] = []
        self.columns_calls: list[tuple[object, str | None, str | None]] = []
        self.rerun_called = False

    def container(self, *, key: str) -> FakeHeaderContainer:
        self.markdowns.append(key)
        return FakeHeaderContainer(self)

    def columns(
        self,
        spec: object,
        *,
        gap: str | None = None,
        vertical_alignment: str | None = None,
    ) -> list[FakeHeaderContext]:
        self.columns_calls.append((spec, gap, vertical_alignment))
        count = len(spec) if isinstance(spec, list) else int(spec)
        return [FakeHeaderContext() for _ in range(count)]

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append(body)

    def button(self, label: str, **kwargs) -> bool:
        self.buttons.append({"label": label, **kwargs})
        return kwargs.get("key") == self.clicked_key

    def download_button(self, label: str, **kwargs) -> None:
        self.buttons.append({"label": label, **kwargs})

    def link_button(self, label: str, url: str, **kwargs) -> None:
        self.buttons.append({"label": label, "url": url, **kwargs})

    def rerun(self) -> None:
        self.rerun_called = True


def test_work_header_home_button_navigates_to_main_without_clearing_session(
    monkeypatch,
) -> None:
    components = importlib.import_module("frontend.work.header")
    fake_st = FakeHeaderStreamlit(clicked_key="work-main-link")
    fake_st.session_state["auth_access_token"] = "jwt-token"
    navigated_pages: list[str] = []

    monkeypatch.setattr(components, "st", fake_st)
    monkeypatch.setattr(components, "navigate_to", navigated_pages.append)

    components.render_header()

    home_button = next(
        button for button in fake_st.buttons if button.get("key") == "work-main-link"
    )
    assert home_button["label"] == components.HOME_BUTTON_LABEL
    assert home_button["help"] == components.HOME_BUTTON_HELP
    assert navigated_pages == ["main"]
    assert fake_st.session_state["auth_access_token"] == "jwt-token"
    assert fake_st.rerun_called is True
    assert not any('href="?page=main"' in body for body in fake_st.markdowns)


def test_work_header_refreshes_cached_profile_when_display_name_missing(monkeypatch) -> None:
    components = importlib.import_module("frontend.work.header")
    session_state = {
        "auth_access_token": "jwt-token",
        "auth_user_email": "manatoki74@gmail.com",
        components.WORK_HEADER_PROFILE_TOKEN_KEY: "jwt-token",
        components.WORK_HEADER_PROFILE_KEY: {"email": "manatoki74@gmail.com"},
    }
    request_calls = []

    def fake_request_me(access_token: str) -> dict:
        request_calls.append(access_token)
        return {"display_name": "닉네임", "email": "manatoki74@gmail.com"}

    monkeypatch.setattr(components, "st", SimpleNamespace(session_state=session_state))
    monkeypatch.setattr(components, "request_me", fake_request_me)

    profile = components._get_work_header_profile()

    assert request_calls == ["jwt-token"]
    assert profile["display_name"] == "닉네임"
    assert session_state[components.WORK_HEADER_PROFILE_KEY]["display_name"] == "닉네임"
