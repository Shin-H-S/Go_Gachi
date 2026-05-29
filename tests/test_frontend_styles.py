from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
STYLES_FILE = ROOT_DIR / "frontend" / "styles.py"


def test_radio_indicator_keeps_unselected_circle_white() -> None:
    styles = STYLES_FILE.read_text(encoding="utf-8")

    assert 'input[type="radio"]' in styles
    assert 'background-color: #ffffff !important;' in styles
    assert 'box-shadow: inset 0 0 0 2px #ffffff !important;' in styles


def test_section_labels_render_at_twenty_pixels() -> None:
    styles = STYLES_FILE.read_text(encoding="utf-8")

    assert "p.section-label" in styles
    assert "p.detail-choice-label" in styles
    assert "font-size: 20px !important;" in styles
