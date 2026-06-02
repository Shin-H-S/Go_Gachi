import ast
import base64
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"
FRONTEND_IMAGE_UTILS = ROOT_DIR / "frontend" / "image_utils.py"
FRONTEND_MAIN_PAGE = ROOT_DIR / "frontend" / "pages" / "main.py"
FRONTEND_WORK_PAGE = ROOT_DIR / "frontend" / "pages" / "work.py"
FRONTEND_WORK_GENERATION = ROOT_DIR / "frontend" / "work_generation.py"
FRONTEND_STYLES = ROOT_DIR / "frontend" / "styles.py"


def test_frontend_config_exposes_preset_helpers() -> None:
    from frontend.config import (
        CHANNEL_SLUGS,
        FORMAT_OPTIONS,
        format_size_label,
        get_detail_id,
        get_detail_size,
    )

    assert FORMAT_OPTIONS["인스타그램"]["value"] == "instagram_square"
    assert CHANNEL_SLUGS["인스타그램"] == "instagram_square"
    assert get_detail_id("인스타그램", "정사각형 피드") == "square_feed"
    assert get_detail_size("인스타그램", "정사각형 피드") == (1080, 1080)
    assert format_size_label((1080, 1080)) == "1080 x 1080"


def test_frontend_config_can_load_presets_from_backend(monkeypatch) -> None:
    from frontend import config

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, list[dict[str, object]]]:
            return {
                "presets": [
                    {
                        "id": "custom_channel",
                        "label": "테스트 채널",
                        "width": 100,
                        "height": 200,
                        "details": [
                            {
                                "id": "custom_detail",
                                "label": "테스트 상세",
                                "width": 300,
                                "height": 400,
                            }
                        ],
                    }
                ]
            }

    def fake_get(url: str, timeout: int) -> FakeResponse:
        assert url == f"{config.BACKEND_URL}/api/config"
        assert timeout == 2
        return FakeResponse()

    monkeypatch.setattr(config.httpx, "get", fake_get)

    options = config._format_options_from_presets(config._load_backend_presets())

    assert options["테스트 채널"]["value"] == "custom_channel"
    assert options["테스트 채널"]["details"][0]["id"] == "custom_detail"
    assert options["테스트 채널"]["details"][0]["size"] == (300, 400)


def test_frontend_config_falls_back_to_local_presets(monkeypatch) -> None:
    from frontend import config

    def fake_get(*args, **kwargs):  # noqa: ANN002, ANN003
        raise config.httpx.ConnectError("backend down")

    monkeypatch.setattr(config, "FRONTEND_CONFIG_SOURCE", "auto")
    monkeypatch.setattr(config, "FRONTEND_USE_MOCK", False)
    monkeypatch.setattr(config.httpx, "get", fake_get)

    presets = config.load_presets()

    assert presets[0]["id"] == "instagram_square"


def test_image_utils_builds_preview_canvas_and_data_url() -> None:
    from frontend.image_utils import bytes_to_data_url, make_preview_canvas

    source = BytesIO()
    Image.new("RGB", (8, 4), "#225544").save(source, format="PNG")

    preview_bytes = make_preview_canvas(
        source.getvalue(),
        "인스타그램",
        "정사각형 피드",
    )
    preview = Image.open(BytesIO(preview_bytes))

    assert preview.size == (1080, 1080)
    assert bytes_to_data_url(b"abc") == "data:image/png;base64,YWJj"


def test_api_client_converts_uploads_and_feedback() -> None:
    from frontend.api_client import build_feedback, data_url_to_bytes, file_to_data_url

    uploaded_file = SimpleNamespace(
        type="image/png",
        getvalue=lambda: b"image-bytes",
    )
    data_url = file_to_data_url(uploaded_file)

    assert data_url == f"data:image/png;base64,{base64.b64encode(b'image-bytes').decode('ascii')}"
    assert data_url_to_bytes(data_url) == b"image-bytes"
    assert (
        build_feedback("  크게 보여줘  ", "정사각형 피드")
        == "광고 유형: 정사각형 피드\n크게 보여줘"
    )


def test_app_delegates_split_module_responsibilities() -> None:
    app_source = FRONTEND_APP.read_text(encoding="utf-8")
    work_source = FRONTEND_WORK_PAGE.read_text(encoding="utf-8")
    generation_source = FRONTEND_WORK_GENERATION.read_text(encoding="utf-8")
    tree = ast.parse(app_source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    defined_functions = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }

    assert FRONTEND_APP.read_text(encoding="utf-8").count("\n") + 1 <= 80
    assert {"pages.main", "pages.work", "router", "styles"}.issubset(imported_modules)
    assert {"api_client", "config", "image_utils", "upload_utils"}.isdisjoint(
        imported_modules
    )
    assert defined_functions.isdisjoint(
        {
            "add_css",
            "build_feedback",
            "create_mock_banner",
            "data_url_to_bytes",
            "file_to_data_url",
            "load_format_options",
            "make_preview_canvas",
        }
    )
    assert "FRONTEND_USE_MOCK" not in app_source
    assert "NETWORK_ERROR" in generation_source
    assert "build_result_context" in work_source
    assert "sync_result_state" in work_source
    assert "result_context" in work_source


def test_large_frontend_modules_are_split_for_review() -> None:
    frontend_files = list((ROOT_DIR / "frontend").rglob("*.py"))
    oversized_files = [
        path.relative_to(ROOT_DIR).as_posix()
        for path in frontend_files
        if path.read_text(encoding="utf-8").count("\n") + 1 > 200
    ]

    assert oversized_files == []


def test_styles_are_composed_from_reviewable_modules() -> None:
    styles_source = FRONTEND_STYLES.read_text(encoding="utf-8")

    assert "from style_base import BASE_CSS" in styles_source
    assert "from style_main_layout import MAIN_LAYOUT_CSS" in styles_source
    assert "from style_work_preview import WORK_PREVIEW_CSS" in styles_source
    assert "def build_css()" in styles_source


def test_work_page_delegates_components_state_and_generation() -> None:
    work_source = FRONTEND_WORK_PAGE.read_text(encoding="utf-8")

    assert "from work_components import" in work_source
    assert "from work_generation import handle_generation_request" in work_source
    assert "from work_preview import render_image_preview" in work_source
    assert "from work_state import" in work_source
    assert "def build_result_context" not in work_source
    assert "def render_channel_tabs" not in work_source
    assert "def create_mock_banner" not in work_source


def test_image_utils_is_a_compatibility_export_layer() -> None:
    image_utils_source = FRONTEND_IMAGE_UTILS.read_text(encoding="utf-8")

    assert "from image_data import bytes_to_data_url" in image_utils_source
    assert "from mock_banner import create_mock_banner" in image_utils_source
    assert "from preview_canvas import make_preview_canvas" in image_utils_source
    assert "def create_mock_banner" not in image_utils_source
    assert "def make_preview_canvas" not in image_utils_source
