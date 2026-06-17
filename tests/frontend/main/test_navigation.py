import importlib


def test_main_nav_keeps_login_signup_links_for_guest(monkeypatch) -> None:
    navigation = importlib.import_module("frontend.main.navigation")
    fake_st = FakeNavigationStreamlit()

    monkeypatch.setattr(navigation, "st", fake_st)

    navigation.render_main_navigation()

    rendered_html = "\n".join(fake_st.markdowns)
    assert 'href="?page=login"' in rendered_html
    assert 'href="?page=signup"' in rendered_html
    assert "\ub85c\uadf8\uc778</a>" in rendered_html
    assert "\ud68c\uc6d0\uac00\uc785</a>" in rendered_html
    assert "\ub85c\uadf8\uc778/a>" not in rendered_html
    assert "\ud68c\uc6d0\uac00\uc785/a>" not in rendered_html
    assert not any(button.get("key") == "main-logout-button" for button in fake_st.buttons)


def test_main_nav_shows_only_logout_button_for_logged_in_user(monkeypatch) -> None:
    navigation = importlib.import_module("frontend.main.navigation")
    fake_st = FakeNavigationStreamlit()
    fake_st.session_state["is_logged_in"] = True
    fake_st.session_state["auth_access_token"] = "jwt-token"

    monkeypatch.setattr(navigation, "st", fake_st)

    navigation.render_main_navigation()

    rendered_html = "\n".join(fake_st.markdowns)
    assert 'href="?page=login"' not in rendered_html
    assert 'href="?page=signup"' not in rendered_html
    assert any(
        button.get("key") == "main-logout-button"
        and button.get("label") == "\ub85c\uadf8\uc544\uc6c3"
        for button in fake_st.buttons
    )


def test_main_logout_button_clears_session_and_stays_on_main(monkeypatch) -> None:
    navigation = importlib.import_module("frontend.main.navigation")
    fake_st = FakeNavigationStreamlit(clicked_key="main-logout-button")
    fake_st.session_state["is_logged_in"] = True
    fake_st.session_state["auth_access_token"] = "jwt-token"
    fake_st.session_state["auth_user_id"] = "user-123"
    fake_st.session_state["auth_user_email"] = "owner@example.com"
    navigated_pages: list[str] = []

    monkeypatch.setattr(navigation, "st", fake_st)
    monkeypatch.setattr(navigation, "navigate_to", navigated_pages.append)

    navigation.render_main_navigation()

    assert fake_st.session_state["is_logged_in"] is False
    assert fake_st.session_state["auth_access_token"] == ""
    assert fake_st.session_state["auth_user_id"] == ""
    assert fake_st.session_state["auth_user_email"] == ""
    assert fake_st.session_state["auth_notice"] == (
        "\ub85c\uadf8\uc544\uc6c3\ub418\uc5c8\uc2b5\ub2c8\ub2e4."
    )
    assert navigated_pages == ["main"]
    assert fake_st.rerun_called is True


class FakeNavigationStreamlit:
    def __init__(self, clicked_key: str | None = None) -> None:
        self.session_state: dict[str, object] = {}
        self.clicked_key = clicked_key
        self.markdowns: list[str] = []
        self.buttons: list[dict[str, object]] = []
        self.rerun_called = False

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append(body)

    def button(self, label: str, **kwargs) -> bool:
        self.buttons.append({"label": label, **kwargs})
        return kwargs.get("key") == self.clicked_key

    def rerun(self) -> None:
        self.rerun_called = True
