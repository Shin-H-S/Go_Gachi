from typing import Literal

CopyMode = Literal["preserve", "polish", "rewrite"]
CopyModeOption = tuple[str, CopyMode]

COPY_MODE_OPTIONS: tuple[CopyModeOption, ...] = (
    ("그대로 사용", "preserve"),
    ("자연스럽게 다듬기", "polish"),
    ("홍보 문구로 바꾸기", "rewrite"),
)

