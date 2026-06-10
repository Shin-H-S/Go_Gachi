from pathlib import Path

from frontend.work.copy import COPY_MODE_LABELS, COPY_MODE_OPTIONS, copy_mode_label

ROOT_DIR = Path(__file__).resolve().parents[2]
COPY_SOURCE = ROOT_DIR / "frontend" / "work" / "copy.py"


def test_frontend_copy_module_does_not_generate_hardcoded_ad_copy() -> None:
    source = COPY_SOURCE.read_text(encoding="utf-8")

    assert "build_auto_copy" not in source
    assert "오늘 가장 맛있는 한 컷" not in source
    assert "지금 저장하기" not in source


def test_copy_mode_options_use_backend_values_and_korean_labels() -> None:
    assert COPY_MODE_OPTIONS == (
        ("그대로 사용", "preserve"),
        ("자연스럽게 다듬기", "polish"),
        ("홍보 문구로 바꾸기", "rewrite"),
    )


def test_copy_mode_labels_are_derived_from_options() -> None:
    assert COPY_MODE_LABELS == {mode: label for label, mode in COPY_MODE_OPTIONS}
    assert copy_mode_label("polish") == "자연스럽게 다듬기"
    assert copy_mode_label("custom") == "custom"
    assert copy_mode_label(None) == "문구"

