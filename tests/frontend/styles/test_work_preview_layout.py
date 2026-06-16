from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
STYLE_WORK_CONTROLS_FILE = ROOT_DIR / "frontend" / "css" / "work_controls.py"
STYLE_WORK_FORMS_FILE = ROOT_DIR / "frontend" / "css" / "work_forms.py"
STYLE_WORK_LOADING_FILE = ROOT_DIR / "frontend" / "css" / "work_loading.py"
STYLE_WORK_PREVIEW_FILE = ROOT_DIR / "frontend" / "css" / "work_preview.py"
STYLE_RESPONSIVE_FILE = ROOT_DIR / "frontend" / "css" / "responsive.py"
WORK_PAGE_FILE = ROOT_DIR / "frontend" / "pages" / "work.py"


def test_work_left_options_are_grouped_in_one_scroll_panel() -> None:
    source = WORK_PAGE_FILE.read_text(encoding="utf-8")
    styles = STYLE_WORK_FORMS_FILE.read_text(encoding="utf-8")

    assert 'st.container(border=True, key="left-options-panel")' in source
    assert 'st.container(border=True, key="left-upload-section")' not in source
    assert 'st.container(border=True, key="left-channel-section")' not in source
    assert 'st.container(border=True, key="left-type-section")' not in source
    assert 'st.container(border=True, key="left-prompt-section")' not in source
    assert ".st-key-left-options-panel" in styles
    assert "height: var(--work-preview-height, 620px);" in styles
    assert "max-height: var(--work-preview-height, 620px);" in styles
    assert "overflow-y: auto;" in styles
    assert "overflow-x: hidden;" in styles
    assert "scrollbar-gutter: stable;" in styles


def test_work_preview_height_is_shared_by_desktop_mobile_and_left_panel() -> None:
    preview_styles = STYLE_WORK_PREVIEW_FILE.read_text(encoding="utf-8")
    responsive_styles = STYLE_RESPONSIVE_FILE.read_text(encoding="utf-8")
    form_styles = STYLE_WORK_FORMS_FILE.read_text(encoding="utf-8")

    assert "--work-preview-height: 620px;" in preview_styles
    assert "--work-generate-button-height: 60px;" in preview_styles
    assert "height: var(--work-preview-height, 620px);" in preview_styles
    assert "height: var(--work-preview-height, 620px);" in form_styles
    assert "--work-preview-height: 360px;" in responsive_styles
    assert ".preview-shell {\n        height: 360px;" not in responsive_styles


def test_work_loading_tips_auto_cycle_without_hover_or_click_trigger() -> None:
    preview_styles = STYLE_WORK_LOADING_FILE.read_text(encoding="utf-8")

    assert "@font-face" in preview_styles
    assert "Cafe24Dongdong" in preview_styles
    assert "noonfonts_twelve@1.1/Cafe24Dongdong.woff" in preview_styles
    assert ".preview-shell .loading-tip-stage" in preview_styles
    assert "--loading-tip-cycle: 119s;" in preview_styles
    assert "--loading-tip-step: 7s;" in preview_styles
    assert (
        "animation: loading-tip-card-cycle var(--loading-tip-cycle) linear infinite;"
        in preview_styles
    )
    assert "animation-delay: calc(var(--tip-index) * var(--loading-tip-step));" in preview_styles
    assert "@keyframes loading-tip-card-cycle" in preview_styles
    assert ".loading-progress-dots span" in preview_styles
    assert ".loading-tip-card::before" not in preview_styles
    assert ".loading-tip-card::after" not in preview_styles
    assert "radial-gradient" not in preview_styles
    assert "#202725" not in preview_styles
    assert "#5A514B" in preview_styles
    assert "#46514d" not in preview_styles
    assert "grid-template-rows: minmax(0, 1fr) auto 25%;" in preview_styles
    assert ".loading-clay-icon-wrap" in preview_styles
    assert ".loading-clay-icon" in preview_styles
    assert "width: clamp(132px, 32%, 178px);" in preview_styles
    assert "aspect-ratio: 1;" in preview_styles
    assert "object-fit: contain;" in preview_styles
    assert "margin: 0 auto 18px;" in preview_styles
    assert ".loading-tip-heading" in preview_styles
    assert ".loading-tip-content strong" in preview_styles
    assert ".loading-tip-content p" in preview_styles
    assert "font-size: 21px;" in preview_styles
    assert "font-weight: 700;" in preview_styles
    assert "font-family: Cafe24Dongdong" in preview_styles
    assert "text-shadow: 0 -1px 0 rgba(255, 255, 255, 0.18);" in preview_styles
    assert "rgba(255, 250, 235" not in preview_styles
    assert "backdrop-filter" not in preview_styles
    assert ".loading-tip-stage:hover" not in preview_styles
    assert ".loading-tip-stage:active" not in preview_styles


def test_work_columns_give_left_panel_more_room_with_medium_gap() -> None:
    source = WORK_PAGE_FILE.read_text(encoding="utf-8")

    assert 'st.columns([0.4, 0.6], gap="medium")' in source


def test_generate_button_sits_below_left_scroll_panel() -> None:
    source = WORK_PAGE_FILE.read_text(encoding="utf-8")
    nested_marker = "                st.markdown("
    outer_marker = "        st.markdown("

    assert f'{nested_marker}\'<div class="generate-button-marker"></div>\'' not in source
    assert f'{outer_marker}\'<div class="generate-button-marker"></div>\'' in source
    assert 'use_container_width=True, type="primary")' in source


def test_generate_button_matches_preview_history_button_height_with_thicker_border() -> None:
    styles = STYLE_WORK_CONTROLS_FILE.read_text(encoding="utf-8")

    generate_styles = styles.split(":has(.generate-button-marker)", 1)[1].split(
        ".st-key-work-preview-undo button",
        1,
    )[0]

    assert "min-height: 60px !important;" in generate_styles
    assert "min-height: var(--work-generate-button-height, 60px) !important;" in generate_styles
    assert "border: 2px solid #0f4cbd !important;" in generate_styles
    assert "border: 2px solid #0b3e9e !important;" in generate_styles
