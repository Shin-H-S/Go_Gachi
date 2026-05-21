"""요청/응답 데이터 형태 정의 (Pydantic).

여기 정의한 모델들이 'API 신청서 양식' 역할을 한다. 들어온 값이 양식에 안 맞으면
(형식/길이 위반 등) FastAPI 가 자동으로 검증해 422 오류로 막아준다.
"""

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Placement(StrEnum):
    """광고를 올릴 위치 코드. 출력 이미지 크기를 결정하는 기준이 된다.

    문자열 Enum 이라 프론트의 select 값(예: "instagram_feed")을 그대로 받는다.
    """

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
    """이미지 크기(픽셀). 256~4096 범위만 허용한다."""

    width: int = Field(..., ge=256, le=4096)
    height: int = Field(..., ge=256, le=4096)


class AdGenerationInput(BaseModel):
    """광고 생성 요청 입력. 라우터가 폼 값을 모아 이 모델로 검증한다.

    필수(industry/mood/ad_type/objective)는 비어 있으면 안 되고, 나머지는 선택이다.
    선택 필드는 채워져 있으면 프롬프트 품질을 높이는 데 쓰인다.
    """

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
        """입력 문자열의 앞뒤 공백을 제거하고, 빈 값은 None 으로 통일한다.

        Args:
            value: 검증 전 원본 문자열(없을 수 있음).
        Returns:
            공백을 정리한 문자열. 비어 있으면 None.
        """
        # 빈 문자열은 None으로 통일해서 프롬프트에 의미 없는 줄이 들어가지 않게 합니다.
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class GeneratedAsset(BaseModel):
    """생성 결과 응답. 프론트는 image_url 을 붙여 결과 이미지를 미리보기 한다."""

    request_id: str
    image_url: str
    filename: str
    size: ImageSize
    prompt: str


class HealthResponse(BaseModel):
    """헬스체크 응답. 서버 상태와 OpenAI 키 설정 여부를 담는다."""

    status: str
    project: str
    environment: str
    openai_enabled: bool
