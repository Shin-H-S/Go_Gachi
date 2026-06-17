from frontend.css.home_navigation import HOME_NAVIGATION_CSS
from frontend.css.work_header import WORK_HEADER_CSS


def test_work_header_download_button_uses_olive_green_with_white_text() -> None:
    assert "#53613b" in WORK_HEADER_CSS
    assert "#27b4c1" not in WORK_HEADER_CSS
    assert "#20a6b2" not in WORK_HEADER_CSS
    assert "color: #ffffff !important" in WORK_HEADER_CSS
    assert "-webkit-text-fill-color: #ffffff !important" in WORK_HEADER_CSS


def test_home_buttons_share_icon_shape_and_main_navigation_keys() -> None:
    assert ".st-key-work-main-link-control" in HOME_NAVIGATION_CSS
    assert ".st-key-mypage-main-link-control" in HOME_NAVIGATION_CSS
    assert ".st-key-mypage-work-link-control" in HOME_NAVIGATION_CSS
    assert ".home-image-link" not in HOME_NAVIGATION_CSS
    assert 'button[kind="secondary"]' in HOME_NAVIGATION_CSS

    assert "width: 52px !important" in HOME_NAVIGATION_CSS
    assert "min-width: 52px" in HOME_NAVIGATION_CSS
    assert "height: 52px !important" in HOME_NAVIGATION_CSS
    assert "border-radius: 999px !important" in HOME_NAVIGATION_CSS
    assert 'background-image: url("data:image/png;base64,' in HOME_NAVIGATION_CSS
    assert "background-size: 32px 32px !important" in HOME_NAVIGATION_CSS
    assert "font-size: 0 !important" in HOME_NAVIGATION_CSS


def test_work_page_icon_is_scaled_down_inside_shared_button() -> None:
    work_icon_block = HOME_NAVIGATION_CSS.split(
        ".st-key-mypage-work-link-control button",
        1,
    )[1].split("}", 1)[0]

    assert "background-size: 26px 26px !important" in work_icon_block
