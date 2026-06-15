from typing import Literal

CopyMode = Literal["preserve", "polish", "rewrite"]
CopyModeOption = tuple[str, CopyMode]

COPY_MODE_OPTIONS: tuple[CopyModeOption, ...] = (
    ("원본대로 유지하기", "preserve"),
    ("자연스럽게 다듬기", "polish"),
    ("홍보 문구로 바꾸기", "rewrite"),
)

COPY_MODE_LABELS: dict[str, str] = {mode: label for label, mode in COPY_MODE_OPTIONS}


def copy_mode_label(mode: object, default: str = "문구") -> str:
    mode_text = str(mode or "")
    return COPY_MODE_LABELS.get(mode_text, mode_text or default)
