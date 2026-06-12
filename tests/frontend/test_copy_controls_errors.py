from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
COPY_CONTROLS = ROOT_DIR / "frontend" / "work" / "copy_controls.py"


def test_copy_controls_do_not_depend_on_auto_copy_backend_flow() -> None:
    source = COPY_CONTROLS.read_text(encoding="utf-8")

    assert "_fill_auto_copy" not in source
    assert "request_auto_copy" not in source
    assert "auto_copy_status" not in source
