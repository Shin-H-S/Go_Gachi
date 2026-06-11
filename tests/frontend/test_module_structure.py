import ast
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_APP = ROOT_DIR / "frontend" / "app.py"
FRONTEND_IMAGE_UTILS = ROOT_DIR / "frontend" / "media" / "image_utils.py"
FRONTEND_WORK_PAGE = ROOT_DIR / "frontend" / "pages" / "work.py"
FRONTEND_WORK_GENERATION = ROOT_DIR / "frontend" / "work" / "generation.py"
FRONTEND_STYLES = ROOT_DIR / "frontend" / "styles.py"


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
    defined_functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    assert app_source.count("\n") + 1 <= 80
    assert {
        "frontend.core.router",
        "frontend.pages.main",
        "frontend.pages.work",
        "frontend.styles",
    }.issubset(imported_modules)
    assert {"api_client", "config", "image_utils", "upload_utils"}.isdisjoint(imported_modules)
    assert defined_functions.isdisjoint(
        {
            "add_css",
            "build_user_prompt",
            "create_mock_banner",
            "data_url_to_bytes",
            "file_to_data_url",
            "load_format_options",
            "make_preview_canvas",
        }
    )
    assert "FRONTEND_USE_MOCK" not in app_source
    assert "FRONTEND_USE_MOCK" not in generation_source
    assert "create_mock_banner" not in generation_source
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

    assert "from frontend.css.base import BASE_CSS" in styles_source
    assert "from frontend.css.main_layout import MAIN_LAYOUT_CSS" in styles_source
    assert "from frontend.css.work_preview import WORK_PREVIEW_CSS" in styles_source
    assert "def build_css()" in styles_source


def test_work_page_delegates_components_state_and_generation() -> None:
    work_source = FRONTEND_WORK_PAGE.read_text(encoding="utf-8")

    assert "from frontend.work.components import" in work_source
    assert "from frontend.work.generation import handle_generation_request" in work_source
    assert "from frontend.work.result_panel import render_result_panel" in work_source
    assert "from frontend.work.state import" in work_source
    assert "def build_result_context" not in work_source
    assert "def render_channel_tabs" not in work_source
    assert "def create_mock_banner" not in work_source


def test_image_utils_is_a_compatibility_export_layer() -> None:
    image_utils_source = FRONTEND_IMAGE_UTILS.read_text(encoding="utf-8")

    assert "from frontend.media.image_data import bytes_to_data_url" in image_utils_source
    assert "from frontend.media.preview_canvas import make_preview_canvas" in image_utils_source
    assert "mock_banner" not in image_utils_source
    assert "def make_preview_canvas" not in image_utils_source


def test_frontend_mock_mode_env_is_not_documented() -> None:
    env_example = (ROOT_DIR / "frontend" / ".env.example").read_text(encoding="utf-8")
    readme = (ROOT_DIR / "frontend" / "README.md").read_text(encoding="utf-8")
    config_source = (ROOT_DIR / "frontend" / "core" / "config.py").read_text(encoding="utf-8")

    assert "FRONTEND_USE_MOCK" not in env_example
    assert "FRONTEND_USE_MOCK" not in readme
    assert "FRONTEND_USE_MOCK" not in config_source
