import ast
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_WORK_PAGE = ROOT_DIR / "frontend" / "pages" / "work.py"
FRONTEND_LOGO_CONTROLS = ROOT_DIR / "frontend" / "work" / "logo_controls.py"
FRONTEND_RESULT_SUMMARY = ROOT_DIR / "frontend" / "work" / "result_summary.py"


def _file_uploader_calls(tree: ast.AST) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "file_uploader"
    ]


def _st_call_with_key(tree: ast.AST, function_name: str, key: str) -> ast.Call | None:
    return next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
            and node.func.attr == function_name
            and any(
                keyword.arg == "key"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value == key
                for keyword in node.keywords
            )
        ),
        None,
    )


def test_logo_uploader_uses_shared_image_type_limit() -> None:
    tree = ast.parse(FRONTEND_LOGO_CONTROLS.read_text(encoding="utf-8"))
    upload_calls = _file_uploader_calls(tree)
    logo_call = _st_call_with_key(tree, "file_uploader", "logo_upload")

    assert upload_calls
    assert logo_call is not None
    type_keyword = next((keyword for keyword in logo_call.keywords if keyword.arg == "type"), None)
    assert isinstance(type_keyword, ast.keyword)
    assert isinstance(type_keyword.value, ast.Name)
    assert type_keyword.value.id == "UPLOAD_FILE_TYPES"
    multiple_keyword = next(
        (keyword for keyword in logo_call.keywords if keyword.arg == "accept_multiple_files"),
        None,
    )
    assert isinstance(multiple_keyword, ast.keyword)
    assert isinstance(multiple_keyword.value, ast.Constant)
    assert multiple_keyword.value.value is False


def test_logo_uploader_does_not_hide_native_remove_button() -> None:
    logo_source = FRONTEND_LOGO_CONTROLS.read_text(encoding="utf-8")

    assert "st.file_uploader" in logo_source
    assert "if logo_file is not None" not in logo_source
    assert "display: none !important;" not in logo_source
    assert 'data-testid="stFileUploaderFile"' not in logo_source


def test_logo_preview_is_rendered_as_separate_work_page_box() -> None:
    work_tree = ast.parse(FRONTEND_WORK_PAGE.read_text(encoding="utf-8"))
    logo_source = FRONTEND_LOGO_CONTROLS.read_text(encoding="utf-8")
    logo_tree = ast.parse(logo_source)

    assert _st_call_with_key(work_tree, "container", "left-logo-preview-section") is not None
    assert any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "render_logo_preview"
        for node in ast.walk(work_tree)
    )

    preview_function = next(
        (
            node
            for node in ast.walk(logo_tree)
            if isinstance(node, ast.FunctionDef) and node.name == "render_logo_preview"
        ),
        None,
    )
    assert preview_function is not None
    markdown_call = next(
        (
            node
            for node in ast.walk(preview_function)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
            and node.func.attr == "markdown"
        ),
        None,
    )

    assert markdown_call is not None
    assert any(
        keyword.arg == "unsafe_allow_html"
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value is True
        for keyword in markdown_call.keywords
    )
    assert "logo-preview-frame" in logo_source
    assert "로고 이미지" in logo_source
    assert all(
        not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
            and node.func.attr in {"image", "caption"}
        )
        for node in ast.walk(preview_function)
    )


def test_logo_controls_and_preview_boxes_share_one_row() -> None:
    tree = ast.parse(FRONTEND_WORK_PAGE.read_text(encoding="utf-8"))
    columns_call = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "st"
            and node.func.attr == "columns"
            and node.args
            and isinstance(node.args[0], ast.List)
            and len(node.args[0].elts) == 2
            and all(isinstance(elt, ast.Constant) for elt in node.args[0].elts)
            and [elt.value for elt in node.args[0].elts] == [0.52, 0.48]
        ),
        None,
    )

    assert columns_call is not None


def test_logo_position_selectbox_uses_shared_backend_supported_values() -> None:
    tree = ast.parse(FRONTEND_LOGO_CONTROLS.read_text(encoding="utf-8"))
    selectbox_call = _st_call_with_key(tree, "selectbox", "logo_position")

    assert selectbox_call is not None
    options_keyword = next(
        (keyword for keyword in selectbox_call.keywords if keyword.arg == "options"),
        None,
    )
    assert isinstance(options_keyword, ast.keyword)
    assert isinstance(options_keyword.value, ast.Name)
    assert options_keyword.value.id == "LOGO_POSITION_OPTIONS"
    index_keyword = next(
        (keyword for keyword in selectbox_call.keywords if keyword.arg == "index"), None
    )
    assert isinstance(index_keyword, ast.keyword)
    assert isinstance(index_keyword.value, ast.Call)


def test_logo_position_labels_are_shared_by_controls_and_result_summary() -> None:
    controls_source = FRONTEND_LOGO_CONTROLS.read_text(encoding="utf-8")
    summary_source = FRONTEND_RESULT_SUMMARY.read_text(encoding="utf-8")

    assert "from frontend.work.logo_positions import" in controls_source
    assert "from frontend.work.logo_positions import LOGO_POSITION_LABELS" in summary_source
    assert "LOGO_POSITION_LABELS = {" not in controls_source
    assert "LOGO_POSITION_LABELS = {" not in summary_source
