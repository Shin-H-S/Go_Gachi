from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
STYLE_BASE_FILE = ROOT_DIR / "frontend" / "css" / "base.py"
STYLE_WORK_CONTROLS_FILE = ROOT_DIR / "frontend" / "css" / "work_controls.py"
STYLE_WORK_HEADER_FILE = ROOT_DIR / "frontend" / "css" / "work_header.py"
STYLE_WORK_PREVIEW_FILE = ROOT_DIR / "frontend" / "css" / "work_preview.py"
STYLE_WORK_SELECTION_FILE = ROOT_DIR / "frontend" / "css" / "work_selection.py"
STYLE_WORK_FORMS_FILE = ROOT_DIR / "frontend" / "css" / "work_forms.py"
STYLE_WORK_UPLOAD_FILE = ROOT_DIR / "frontend" / "css" / "work_upload.py"
FRONTEND_STYLES_FILE = ROOT_DIR / "frontend" / "styles.py"


def test_radio_indicator_keeps_unselected_circle_white() -> None:
    styles = STYLE_WORK_SELECTION_FILE.read_text(encoding="utf-8")

    assert 'input[type="radio"]' in styles
    assert "background-color: #ffffff !important;" in styles
    assert "box-shadow: inset 0 0 0 2px #ffffff !important;" in styles


def test_mypage_styles_load_after_global_work_button_styles() -> None:
    source = FRONTEND_STYLES_FILE.read_text(encoding="utf-8")
    css_parts = source.split("CSS_PARTS = [", 1)[1].split("]", 1)[0]

    assert css_parts.index("WORK_CONTROLS_CSS") < css_parts.index("MYPAGE_CSS")


def test_work_header_styles_override_global_work_button_styles() -> None:
    source = FRONTEND_STYLES_FILE.read_text(encoding="utf-8")
    css_parts = source.split("CSS_PARTS = [", 1)[1].split("]", 1)[0]

    assert css_parts.index("WORK_CONTROLS_CSS") < css_parts.index("WORK_HEADER_CSS")


def test_section_labels_render_at_twenty_pixels() -> None:
    styles = STYLE_WORK_FORMS_FILE.read_text(encoding="utf-8")

    assert "p.section-label" in styles
    assert "p.detail-choice-label" in styles
    assert "font-size: 20px !important;" in styles


def test_work_header_keeps_original_background_without_divider() -> None:
    styles = STYLE_WORK_HEADER_FILE.read_text(encoding="utf-8")

    assert ".block-container:has(.work-profile-card)" in styles
    assert 'div[data-testid="stMainBlockContainer"]:has(.work-profile-card)' in styles
    assert "padding-top: 12px !important;" in styles
    assert "padding-bottom: 0 !important;" in styles
    assert "margin-bottom: calc(var(--work-generate-button-height, 60px) * -0.55);" in styles
    assert "padding-top: 9px !important;" in styles
    assert ".st-key-work-hero" in styles
    assert "margin: -12px 0 20px;" not in styles
    assert "margin: -9px 0 24px;" not in styles
    assert "#2563c7" not in styles
    assert "width: 100vw;" not in styles
    assert "margin-left: calc(50% - 50vw);" not in styles
    assert "margin-right: calc(50% - 50vw);" not in styles
    assert "background: transparent !important;" in styles
    assert ".topbar" not in styles
    assert "brand-kicker" not in styles
    assert "border-bottom" not in styles


def test_work_mypage_profile_button_is_borderless_card_like_control() -> None:
    styles = STYLE_WORK_HEADER_FILE.read_text(encoding="utf-8")

    assert ".work-profile-card" in styles
    assert ".work-profile-avatar" in styles
    assert ".work-profile-text" in styles
    assert ".st-key-work-mypage-link button" in styles
    assert ".st-key-work-mypage-link button:focus" in styles
    assert ".st-key-work-mypage-link button:active" in styles
    assert 'button[data-testid="stBaseButton-secondary"]' in styles
    assert "border: 0 !important;" in styles
    assert "background: transparent !important;" in styles
    assert "background-color: transparent !important;" in styles
    assert "color: transparent !important;" in styles
    assert "pointer-events: none;" in styles
    assert "z-index: 2;" in styles


def test_header_places_single_download_top_right_and_large_history_under_preview() -> None:
    header_styles = STYLE_WORK_HEADER_FILE.read_text(encoding="utf-8")
    preview_styles = STYLE_WORK_PREVIEW_FILE.read_text(encoding="utf-8")
    control_styles = STYLE_WORK_CONTROLS_FILE.read_text(encoding="utf-8")

    assert ".st-key-work-header-download-button button" in header_styles
    assert ".st-key-work-header-download-fetch button" in header_styles
    assert ".st-key-work-header-download-empty button" in header_styles
    assert "background: #53613b !important;" in header_styles
    assert "border-width: 0 !important;" in header_styles
    assert "opacity: 1 !important;" in header_styles
    assert ".result-download-action" not in preview_styles
    assert ".preview-history-controls" in preview_styles
    assert "width: 100%;" in preview_styles
    assert "margin: 0;" in preview_styles
    assert ".st-key-work-preview-undo button" in control_styles
    assert ".st-key-work-preview-redo button" in control_styles
    assert "min-height: 60px !important;" in control_styles
    assert "font-size: 30px !important;" in control_styles


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
