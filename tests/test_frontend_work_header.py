import importlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
WORK_COMPONENTS = ROOT_DIR / "frontend" / "work" / "components.py"


def test_mypage_navigation_keeps_streamlit_session() -> None:
    source = WORK_COMPONENTS.read_text(encoding="utf-8")

    assert 'href="?page=mypage"' not in source
    assert 'navigate_to("mypage")' in source
    assert 'key="work-mypage-link"' in source


def test_work_header_uses_dedicated_hero_container() -> None:
    source = WORK_COMPONENTS.read_text(encoding="utf-8")

    assert 'st.container(key="work-hero")' in source


def test_work_header_renders_left_mypage_and_right_download_button() -> None:
    source = WORK_COMPONENTS.read_text(encoding="utf-8")

    assert "[0.22, 0.60, 0.18]" in source
    assert "_render_mypage_profile_button()" in source
    assert "_render_header_download_button()" in source
    assert 'key="work-header-download-button"' in source
    assert 'key="work-header-download-fetch"' in source
    assert 'key="work-header-download-empty"' in source
    assert "GO-GACHI CAFE AD MAKER V1" not in source
    assert "brand-kicker" not in source
    assert "topbar" not in source
    assert "<h1" not in source


def test_work_header_profile_markup_is_not_rendered_as_code_block() -> None:
    source = WORK_COMPONENTS.read_text(encoding="utf-8")

    assert "profile_html = (" in source
    assert "st.markdown(profile_html" in source
    assert '<div class="work-profile-card" aria-hidden="true">\n            <div' not in source


def test_work_header_profile_summary_uses_nickname_email_and_avatar() -> None:
    components = importlib.import_module("frontend.work.components")

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
    components = importlib.import_module("frontend.work.components")

    summary = components._build_mypage_profile_summary({}, is_logged_in=False)

    assert summary == {"avatar": "?", "title": "마이페이지", "email": ""}
