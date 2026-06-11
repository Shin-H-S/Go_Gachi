from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
STYLE_BASE_FILE = ROOT_DIR / "frontend" / "css" / "base.py"
STYLE_WORK_SELECTION_FILE = ROOT_DIR / "frontend" / "css" / "work_selection.py"
STYLE_WORK_FORMS_FILE = ROOT_DIR / "frontend" / "css" / "work_forms.py"


def test_radio_indicator_keeps_unselected_circle_white() -> None:
    styles = STYLE_WORK_SELECTION_FILE.read_text(encoding="utf-8")

    assert 'input[type="radio"]' in styles
    assert 'background-color: #ffffff !important;' in styles
    assert 'box-shadow: inset 0 0 0 2px #ffffff !important;' in styles


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


def test_text_overlay_checkbox_label_is_forced_black() -> None:
    styles = STYLE_WORK_SELECTION_FILE.read_text(encoding="utf-8")

    assert ".st-key-text_overlay_enabled" in styles
    assert "color: #111111 !important;" in styles
    assert "-webkit-text-fill-color: #111111 !important;" in styles


def test_streamlit_alert_messages_are_forced_readable() -> None:
    styles = STYLE_BASE_FILE.read_text(encoding="utf-8")

    assert 'div[data-testid="stAlert"]' in styles
    assert 'div[data-testid="stAlert"] *' in styles
    assert "color: #111111 !important;" in styles
    assert "-webkit-text-fill-color: #111111 !important;" in styles
