"""게시 위치별 이미지 프리셋 로딩."""

import json
from functools import lru_cache

from pydantic import BaseModel, Field

from backend.app.core.config import CONFIG_DIR


class PresetDetail(BaseModel):
    """채널 안에서 사용자가 선택하는 상세 광고 유형."""

    id: str
    label: str
    width: int
    height: int
    prompt_hint: str = ""


class Preset(BaseModel):
    """프론트 표시 정보와 OpenAI 요청 크기를 함께 가진 광고 규격."""

    id: str
    label: str
    detail: str
    width: int
    height: int
    api_size: str
    prompt_hint: str
    channel_prompt: str = ""
    details: list[PresetDetail] = Field(default_factory=list)

    def find_detail(self, detail_id: str | None) -> PresetDetail | None:
        """detailType으로 상세 광고 유형을 찾는다."""
        if not detail_id:
            return None
        return next((detail for detail in self.details if detail.id == detail_id), None)


@lru_cache
def get_presets() -> dict[str, Preset]:
    """config/presets.json을 읽어 id 기준 dict로 반환한다."""
    presets_path = CONFIG_DIR / "presets.json"
    raw_presets = json.loads(presets_path.read_text(encoding="utf-8"))
    presets = [Preset(**item) for item in raw_presets]
    return {preset.id: preset for preset in presets}


def default_preset() -> Preset:
    """요청에 presetId가 없을 때 사용할 기본 프리셋."""
    return next(iter(get_presets().values()))
