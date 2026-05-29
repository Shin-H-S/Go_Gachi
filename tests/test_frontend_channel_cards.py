import ast
from pathlib import Path

from PIL import Image

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"
STYLES_FILE = ROOT_DIR / "frontend" / "styles.py"


def test_channel_asset_files_match_preset_ids() -> None:
    from frontend.config import FORMAT_OPTIONS, get_channel_asset_path

    for format_label, option in FORMAT_OPTIONS.items():
        asset_path = get_channel_asset_path(format_label)

        assert asset_path.name == f"{option['value']}.png"
        assert asset_path.exists()


def test_missing_channel_asset_returns_none(monkeypatch, tmp_path) -> None:
    from frontend import config

    format_label = next(iter(config.FORMAT_OPTIONS))
    monkeypatch.setattr(config, "CHANNEL_ASSET_DIR", tmp_path)

    assert config.get_existing_channel_asset_path(format_label) is None


def test_baemin_channel_asset_is_reduced_for_card_ui() -> None:
    from frontend.config import get_channel_asset_path

    asset_path = get_channel_asset_path("배달의 민족")

    with Image.open(asset_path) as image:
        assert image.size == (512, 512)
    assert asset_path.stat().st_size < 500_000


def test_channel_tabs_render_logo_card_media() -> None:
    app_source = FRONTEND_APP.read_text(encoding="utf-8")
    tree = ast.parse(app_source)
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }

    assert "get_existing_channel_asset_path" in imported_names
    assert "channel-card-media" in app_source
    assert "channel-card-placeholder" in app_source


def test_channel_card_styles_keep_fixed_logo_area() -> None:
    styles = STYLES_FILE.read_text(encoding="utf-8")

    assert ".channel-card-media" in styles
    assert ".channel-card-placeholder" in styles
    assert "height: 128px;" in styles
    assert "object-fit: contain;" in styles
