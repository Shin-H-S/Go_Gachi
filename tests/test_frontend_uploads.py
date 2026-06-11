import ast
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_WORK_PAGE = ROOT_DIR / "frontend" / "pages" / "work.py"


def _file_uploader_calls(tree: ast.AST) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "file_uploader"
    ]


def test_menu_uploader_accepts_multiple_files() -> None:
    tree = ast.parse(FRONTEND_WORK_PAGE.read_text(encoding="utf-8"))
    upload_calls = _file_uploader_calls(tree)

    assert upload_calls
    multiple_keyword = next(
        (keyword for keyword in upload_calls[0].keywords if keyword.arg == "accept_multiple_files"),
        None,
    )

    assert isinstance(multiple_keyword, ast.keyword)
    assert isinstance(multiple_keyword.value, ast.Constant)
    assert multiple_keyword.value.value is True


def test_upload_policy_is_shared_constant() -> None:
    from frontend.upload_utils import UPLOAD_FILE_TYPES

    assert UPLOAD_FILE_TYPES == ["jpg", "jpeg", "png", "webp"]


def test_get_primary_uploaded_file_returns_first_file_from_multiple_uploads() -> None:
    from frontend.upload_utils import get_primary_uploaded_file

    first_file = SimpleNamespace(name="first.jpg")
    second_file = SimpleNamespace(name="second.jpg")

    assert get_primary_uploaded_file([first_file, second_file]) is first_file


def test_get_primary_uploaded_file_returns_none_without_uploads() -> None:
    from frontend.upload_utils import get_primary_uploaded_file

    assert get_primary_uploaded_file([]) is None
    assert get_primary_uploaded_file(None) is None
