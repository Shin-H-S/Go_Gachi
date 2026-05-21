"""Pydantic schemas for ad creative generation."""

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Placement(StrEnum):
    # 프론트엔드 select 값과 백엔드 사이즈 프리셋을 연결하는 게시 위치 코드입니다.
    INSTAGRAM_FEED = "instagram_feed"
    INSTAGRAM_STORY = "instagram_story"
    INSTAGRAM_REELS = "instagram_reels"
    FACEBOOK_FEED = "facebook_feed"
    NAVER_PLACE = "naver_place"
    NAVER_BLOG = "naver_blog"
    KAKAO_CHANNEL = "kakao_channel"
    BANNER_LANDSCAPE = "banner_landscape"
    CUSTOM = "custom"


class ImageSize(BaseModel):
    width: int = Field(..., ge=256, le=4096)
    height: int = Field(..., ge=256, le=4096)


class AdGenerationInput(BaseModel):
    # 광고 생성에 필요한 최소 브리프입니다. 선택 필드는 있으면 프롬프트 품질을 높이는 데 씁니다.
    industry: str = Field(..., min_length=1, max_length=80)
    mood: str = Field(..., min_length=1, max_length=80)
    ad_type: str = Field(..., min_length=1, max_length=80)
    objective: str = Field(..., min_length=1, max_length=120)
    placement: Placement = Placement.INSTAGRAM_FEED
    brand_name: Optional[str] = Field(default=None, max_length=80)
    target_audience: Optional[str] = Field(default=None, max_length=120)
    key_message: Optional[str] = Field(default=None, max_length=200)
    offer: Optional[str] = Field(default=None, max_length=120)
    custom_width: Optional[int] = Field(default=None, ge=256, le=4096)
    custom_height: Optional[int] = Field(default=None, ge=256, le=4096)

    @field_validator(
        "industry",
        "mood",
        "ad_type",
        "objective",
        "brand_name",
        "target_audience",
        "key_message",
        "offer",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: Optional[str]) -> Optional[str]:
        # 빈 문자열은 None으로 통일해서 프롬프트에 의미 없는 줄이 들어가지 않게 합니다.
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class GeneratedAsset(BaseModel):
    request_id: str
    image_url: str
    filename: str
    size: ImageSize
    prompt: str


class HealthResponse(BaseModel):
    status: str
    project: str
    environment: str
    openai_enabled: bool
