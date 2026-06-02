import ast
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_WORK_COMPONENTS = ROOT_DIR / "frontend" / "work" / "components.py"
STYLE_WORK_CHANNELS_FILE = ROOT_DIR / "frontend" / "css" / "work_channels.py"


class FakeColumn:
    def __enter__(self) -> "FakeColumn":
        return self

    def __exit__(self, *args) -> None:  # noqa: ANN002
        return None


def import_frontend_module(module_name: str):
    root_path = str(ROOT_DIR)
    if root_path not in sys.path:
        sys.path.insert(0, root_path)

    return importlib.import_module(module_name)


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
    components_source = FRONTEND_WORK_COMPONENTS.read_text(encoding="utf-8")
    tree = ast.parse(components_source)
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }

    assert "get_existing_channel_asset_path" in imported_names
    assert "channel-card-media" in components_source
    assert "channel-card-placeholder" in components_source


def test_channel_tabs_create_one_column_per_configured_preset(monkeypatch) -> None:
    work_components = import_frontend_module("frontend.work.components")
    fake_format_options = {
        "첫 채널": {"value": "first_channel", "details": []},
        "두번째 채널": {"value": "second_channel", "details": []},
        "세번째 채널": {"value": "third_channel", "details": []},
        "네번째 채널": {"value": "fourth_channel", "details": []},
    }
    fake_st = SimpleNamespace(session_state={})

    def fake_columns(count: int, gap: str) -> list[FakeColumn]:
        fake_st.column_count = count
        fake_st.column_gap = gap
        return [FakeColumn() for _ in range(count)]

    fake_st.markdown = lambda *args, **kwargs: None
    fake_st.columns = fake_columns
    fake_st.button = lambda *args, **kwargs: False
    fake_st.rerun = lambda: None

    monkeypatch.setattr(work_components, "FORMAT_OPTIONS", fake_format_options)
    monkeypatch.setattr(
        work_components,
        "CHANNEL_SLUGS",
        {label: option["value"] for label, option in fake_format_options.items()},
    )
    monkeypatch.setattr(work_components, "get_existing_channel_asset_path", lambda label: None)
    monkeypatch.setattr(work_components, "st", fake_st)

    work_components.render_channel_tabs("첫 채널")

    assert fake_st.column_count == len(fake_format_options)
    assert fake_st.column_gap == "small"


def test_channel_card_styles_keep_fixed_logo_area() -> None:
    styles = STYLE_WORK_CHANNELS_FILE.read_text(encoding="utf-8")

    assert ".channel-card-media" in styles
    assert ".channel-card-placeholder" in styles
    assert "height: 128px;" in styles
    assert "object-fit: contain;" in styles
    assert "repeat(3" not in styles
