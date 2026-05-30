import ast
import base64
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"


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
    tree = ast.parse(app_source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    defined_functions = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }

    assert {
        "api_client",
        "config",
        "image_utils",
        "styles",
        "upload_utils",
    }.issubset(imported_modules)
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
    assert "FRONTEND_USE_MOCK" in app_source
    assert "NETWORK_ERROR" in app_source
    assert "build_result_context" in defined_functions
    assert "sync_result_state" in defined_functions
    assert "result_context" in app_source
