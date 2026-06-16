from frontend.css.work_header import WORK_HEADER_CSS


def test_work_header_download_button_uses_olive_green_with_white_text() -> None:
    assert "#53613b" in WORK_HEADER_CSS
    assert "#27b4c1" not in WORK_HEADER_CSS
    assert "#20a6b2" not in WORK_HEADER_CSS
    assert "color: #ffffff !important" in WORK_HEADER_CSS
    assert "-webkit-text-fill-color: #ffffff !important" in WORK_HEADER_CSS
