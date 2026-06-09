"""채널/상세 규격별 텍스트 합성 레이아웃 로딩."""

import json
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.core.config import CONFIG_DIR

TextPosition = Literal[
    "top_left",
    "top_center",
    "bottom_center",
]
TextAlign = Literal["left", "center"]


class TextLayout(BaseModel):
    """후속 overlay_text 모듈이 사용할 텍스트 배치 규칙."""

    position: TextPosition
    safe_margin: int = Field(ge=0)
    max_width_ratio: float = Field(gt=0, le=1)
    headline_font_ratio: float = Field(gt=0, le=0.2)
    subcopy_font_ratio: float = Field(gt=0, le=0.2)
    cta_font_ratio: float = Field(gt=0, le=0.2)
    max_lines: int = Field(ge=1, le=6)
    align: TextAlign
    color: str
    shadow: bool = True
    backdrop: bool = False


@lru_cache
def get_text_layouts() -> dict[str, dict[str, TextLayout]]:
    """config/text_layouts.json을 읽어 채널/상세 유형 기준 dict로 반환한다."""
    layouts_path = CONFIG_DIR / "text_layouts.json"
    raw_layouts = json.loads(layouts_path.read_text(encoding="utf-8"))
    return {
        preset_id: {
            detail_id: TextLayout(**layout)
            for detail_id, layout in detail_layouts.items()
        }
        for preset_id, detail_layouts in raw_layouts.items()
    }


def find_text_layout(preset_id: str, detail_id: str) -> TextLayout:
    """선택한 채널/상세 유형에 맞는 텍스트 배치 규칙을 찾는다."""
    layouts = get_text_layouts()
    try:
        return layouts[preset_id][detail_id]
    except KeyError as exc:
        raise ValueError(
            f"지원하지 않는 텍스트 레이아웃입니다: {preset_id}/{detail_id}"
        ) from exc
