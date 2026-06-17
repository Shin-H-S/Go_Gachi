from pathlib import Path

from frontend.css.main_layout import MAIN_LAYOUT_CSS

ROOT_DIR = Path(__file__).resolve().parents[3]
STYLE_MAIN_VISUAL_FILE = ROOT_DIR / "frontend" / "css" / "main_visual.py"


def test_main_page_styles_match_linktree_inspired_hero() -> None:
    styles = MAIN_LAYOUT_CSS + STYLE_MAIN_VISUAL_FILE.read_text(encoding="utf-8")

    assert ".main-landing" in styles
    assert ".landing-nav" in styles
    assert ".hero-title" in styles
    assert ".blue-slide-track" in styles
    assert "@keyframes blue-panel-slide" in styles
    assert "#d8ff00" in styles
    assert ".landing-login {" in styles
    assert ".landing-signup {" in styles
    assert ".landing-login:hover" in styles
    assert ".landing-signup:hover" in styles
    assert "text-decoration: none !important;" in styles
    landing_block = styles.split(".st-key-main-landing {", 1)[1].split("}", 1)[0]
    assert "min-height: 100vh;" in landing_block
    assert "calc(100vh - 64px)" not in landing_block
    assert ".stApp:has(.st-key-main-landing)" in styles
    assert '[data-testid="stMain"]:has(.st-key-main-landing)' in styles
    assert ".landing-login {\n    background: #eff1ec;\n    color: #0b0e14 !important;" in styles
    assert (
        ".landing-signup {\n"
        "    border-radius: 999px;\n"
        "    background: #1e2433;\n"
        "    color: #ffffff !important;"
    ) in styles
    assert ".st-key-main-logout-button button {" in styles
    logout_container_block = styles.split(".st-key-main-logout-button {", 1)[
        1
    ].split("}", 1)[0]
    logout_button_block = styles.split(".st-key-main-logout-button button {", 1)[
        1
    ].split("}", 1)[0]
    logout_hover_block = styles.split(
        ".st-key-main-logout-button button:hover,",
        1,
    )[1].split("}", 1)[0]
    assert "transform: translateX(-100%);" in logout_container_block
    assert "min-height: 78px !important;" in logout_button_block
    assert "padding: 0 34px !important;" in logout_button_block
    assert "border-radius: 8px !important;" in logout_button_block
    assert "background: #eff1ec !important;" in logout_button_block
    assert "color: #0b0e14 !important;" in logout_button_block
    for visual_rule in (
        "background: #eff1ec !important;",
        "background-color: #eff1ec !important;",
        "color: #0b0e14 !important;",
        "-webkit-text-fill-color: #0b0e14 !important;",
        "border: 0 !important;",
        "border-color: transparent !important;",
        "box-shadow: none !important;",
        "transition: none !important;",
    ):
        assert visual_rule in logout_button_block
        assert visual_rule in logout_hover_block
    assert ".st-key-main-logout-button div[data-testid=\"stButton\"] button," in styles
    assert ".st-key-main-logout-button div[data-testid=\"stButton\"] button:hover," in styles
    assert ".st-key-main-logout-button div[data-testid=\"stButton\"] button:focus," in styles
    assert ".st-key-main-logout-button div[data-testid=\"stButton\"] button:active" in styles
    assert ".st-key-main-logout-button div[data-testid=\"stButton\"] button p," in styles
    assert ".st-key-main-logout-button div[data-testid=\"stButton\"] button:hover p," in styles


def test_main_start_button_keeps_original_cta_visual_contract() -> None:
    styles = MAIN_LAYOUT_CSS
    container_selector = ".st-key-main-start-button {"
    button_selector = ".st-key-main-start-button button {"
    button_base_selector = (
        '.st-key-main-start-button div[data-testid="stButton"] '
        'button[data-testid="stBaseButton-secondary"] {'
    )
    button_text_selector = (
        '.st-key-main-start-button div[data-testid="stButton"]\n'
        '    button[data-testid="stBaseButton-secondary"] * {'
    )

    assert container_selector in styles
    assert button_selector in styles
    assert button_text_selector in styles
    assert button_base_selector in styles
    container_block = styles.split(container_selector, 1)[1].split("}", 1)[0]
    button_block = styles.split(button_selector, 1)[1].split("}", 1)[0]
    button_text_block = styles.split(button_text_selector, 1)[1].split("}", 1)[0]

    assert "width: min(380px, 100%) !important;" in container_block
    assert "display: flex !important;" in button_block
    assert "align-items: center !important;" in button_block
    assert "justify-content: center !important;" in button_block
    assert "min-height: 80px !important;" in button_block
    assert "width: 100% !important;" in button_block
    assert "border-radius: 999px !important;" in button_block
    assert "background: #24551e !important;" in button_block
    assert "background-color: #24551e !important;" in button_block
    assert "background-image: none !important;" in button_block
    assert "font-size: 27.3px !important;" in button_block
    assert "font-weight: 950 !important;" in button_block
    assert "color: #ffffff !important;" in button_block
    assert "-webkit-text-fill-color: #ffffff !important;" in button_block
    assert "box-shadow: 0 18px 34px rgba(36, 85, 30, 0.28) !important;" in button_block
    assert "box-sizing: border-box !important;" in button_block
    assert "color: #ffffff !important;" in button_text_block
    assert "-webkit-text-fill-color: #ffffff !important;" in button_text_block
    assert "font-size: 27.3px !important;" in button_text_block
