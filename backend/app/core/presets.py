"""게시 위치별 이미지 프리셋 로딩."""

import json
from functools import lru_cache

from pydantic import BaseModel

from backend.app.core.config import CONFIG_DIR


class Preset(BaseModel):
    """프론트 표시 정보와 OpenAI 요청 크기를 함께 가진 광고 규격."""

    id: str
    label: str
    detail: str
    width: int
    height: int
    api_size: str
    prompt_hint: str


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
