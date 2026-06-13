from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
STYLE_BASE_FILE = ROOT_DIR / "frontend" / "css" / "base.py"
STYLE_WORK_SELECTION_FILE = ROOT_DIR / "frontend" / "css" / "work_selection.py"
STYLE_WORK_FORMS_FILE = ROOT_DIR / "frontend" / "css" / "work_forms.py"
STYLE_WORK_UPLOAD_FILE = ROOT_DIR / "frontend" / "css" / "work_upload.py"


def test_radio_indicator_keeps_unselected_circle_white() -> None:
    styles = STYLE_WORK_SELECTION_FILE.read_text(encoding="utf-8")

    assert 'input[type="radio"]' in styles
    assert "background-color: #ffffff !important;" in styles
    assert "box-shadow: inset 0 0 0 2px #ffffff !important;" in styles


def test_section_labels_render_at_twenty_pixels() -> None:
    styles = STYLE_WORK_FORMS_FILE.read_text(encoding="utf-8")

    assert "p.section-label" in styles
    assert "p.detail-choice-label" in styles
    assert "font-size: 20px !important;" in styles


def test_segmented_control_grid_does_not_assume_three_presets() -> None:
    styles = STYLE_WORK_SELECTION_FILE.read_text(encoding="utf-8")

    assert "repeat(3" not in styles
    assert "auto-fit" in styles


def test_copy_mode_radio_heading_is_plain_text_not_button_like() -> None:
    styles = STYLE_WORK_SELECTION_FILE.read_text(encoding="utf-8")

    assert ".st-key-copy_mode_label" in styles
    assert 'label:not([data-baseweb="radio"])' in styles
    assert "border: 0 !important;" in styles
    assert "background: #ffffff !important;" in styles
    assert "font-size: 15px !important;" in styles


def test_ad_copy_checkbox_label_is_forced_black() -> None:
    styles = STYLE_WORK_SELECTION_FILE.read_text(encoding="utf-8")

    assert ".st-key-ad_copy_enabled" in styles
    assert ".st-key-text_overlay_enabled" not in styles
    assert "color: #111111 !important;" in styles
    assert "-webkit-text-fill-color: #111111 !important;" in styles


def test_ad_copy_checked_checkbox_icon_stays_visible() -> None:
    styles = STYLE_WORK_SELECTION_FILE.read_text(encoding="utf-8")

    assert '.st-key-ad_copy_enabled input[type="checkbox"]' in styles
    assert '.st-key-ad_copy_enabled label[data-baseweb="checkbox"]' in styles
    assert 'input[type="checkbox"]:checked' in styles
    assert '.st-key-ad_copy_enabled label[data-baseweb="checkbox"] svg' in styles
    assert "fill: #ffffff !important;" in styles
    assert "stroke: #ffffff !important;" in styles


def test_streamlit_alert_messages_are_forced_readable() -> None:
    styles = STYLE_BASE_FILE.read_text(encoding="utf-8")

    assert 'div[data-testid="stAlert"]' in styles
    assert 'div[data-testid="stAlert"] *' in styles
    assert "color: #111111 !important;" in styles
    assert "-webkit-text-fill-color: #111111 !important;" in styles


def test_uploaded_file_chip_is_forced_readable() -> None:
    styles = STYLE_WORK_UPLOAD_FILE.read_text(encoding="utf-8")

    assert 'div[data-testid="stFileUploaderFile"]' in styles
    assert '[data-testid="stFileUploaderFileName"]' in styles
    assert '[data-testid="stFileUploaderFileSize"]' in styles
    assert "background-color: #ffffff !important;" in styles
    assert "color: #202725 !important;" in styles
    assert "-webkit-text-fill-color: #202725 !important;" in styles


def test_work_upload_styles_do_not_include_logo_specific_layout() -> None:
    styles = STYLE_WORK_UPLOAD_FILE.read_text(encoding="utf-8")

    assert ".st-key-left-logo-section" not in styles
    assert ".st-key-left-logo-preview-section" not in styles
    assert ".logo-preview-frame" not in styles
    assert ".logo-preview-placeholder" not in styles
    assert ".st-key-logo_upload" not in styles
