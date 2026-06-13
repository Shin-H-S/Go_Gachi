import ast
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_WORK_PAGE = ROOT_DIR / "frontend" / "pages" / "work.py"


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


def test_work_page_does_not_import_or_render_logo_controls() -> None:
    source = FRONTEND_WORK_PAGE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert "frontend.work.logo_controls" not in source
    assert "render_logo_controls" not in source
    assert "render_logo_preview" not in source
    assert _st_call_with_key(tree, "container", "left-logo-section") is None
    assert _st_call_with_key(tree, "container", "left-logo-preview-section") is None


def test_work_page_does_not_create_logo_uploader_or_position_selector() -> None:
    source = FRONTEND_WORK_PAGE.read_text(encoding="utf-8")

    assert "logo_upload" not in source
    assert "logo_position" not in source
    assert "로고 업로드" not in source
    assert "로고 위치" not in source
    assert "로고 이미지" not in source
