"""게시 위치별 이미지 프리셋 로딩."""

import json
from functools import lru_cache

from pydantic import BaseModel, Field, field_validator

from backend.app.core.config import CONFIG_DIR


class PresetDetail(BaseModel):
    """채널 안에서 사용자가 선택하는 상세 광고 유형."""

    id: str
    label: str
    width: int
    height: int
    api_size: str
    prompt_hint: str = ""

    @field_validator("api_size")
    @classmethod
    def validate_api_size(cls, value: str) -> str:
        """gpt-image-2가 받을 수 있는 이미지 생성 규격인지 확인한다."""
        try:
            width_text, height_text = value.lower().split("x", maxsplit=1)
            width = int(width_text)
            height = int(height_text)
        except ValueError as exc:
            raise ValueError("api_size는 WIDTHxHEIGHT 형식이어야 합니다.") from exc

        if width <= 0 or height <= 0:
            raise ValueError("api_size의 가로/세로는 양수여야 합니다.")
        if width % 16 != 0 or height % 16 != 0:
            raise ValueError("api_size의 가로/세로는 16px 단위여야 합니다.")
        if max(width, height) > 3840:
            raise ValueError("api_size의 최대 변은 3840px 이하여야 합니다.")
        if max(width, height) / min(width, height) > 3:
            raise ValueError("api_size의 장단변 비율은 3:1을 넘을 수 없습니다.")

        pixels = width * height
        if not 655_360 <= pixels <= 8_294_400:
            raise ValueError("api_size의 전체 픽셀 수가 허용 범위를 벗어났습니다.")

        return value


class Preset(BaseModel):
    """게시 채널의 공통 프롬프트와 상세 광고 유형 목록."""

    id: str
    label: str
    prompt_hint: str
    channel_prompt: str = ""
    details: list[PresetDetail] = Field(default_factory=list)

    def find_detail(self, detail_id: str | None) -> PresetDetail | None:
        """detailType으로 상세 광고 유형을 찾는다."""
        if not detail_id:
            return None
        return next((detail for detail in self.details if detail.id == detail_id), None)

    def default_detail(self) -> PresetDetail:
        """detailType이 없을 때 사용할 기본 상세 광고 유형을 반환한다."""
        if not self.details:
            raise ValueError(f"프리셋에 상세 광고 유형이 없습니다: {self.id}")
        return self.details[0]


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
