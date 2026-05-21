"""요청/응답 데이터 형태 (Pydantic).

선택형 입력은 Enum으로 정해진 값만 받는다(잘못된 값 자동 검증).
자유입력(매장명/가격/연락처)은 일반 str로 받는다.
"""

from enum import Enum

from pydantic import BaseModel, Field


class Industry(str, Enum):
    """업종. 우선 음식점부터, 이후 확장."""

    RESTAURANT = "음식점"


class AdPurpose(str, Enum):
    """광고 목적."""

    NEW_OPEN = "신규 오픈 홍보"
    EVENT = "이벤트·할인 안내"
    NEW_MENU = "신메뉴 출시"
    RESERVATION = "예약 유도"
    REVIEW = "후기 강조"
    EXPERTISE = "전문성 강조"
    BRANDING = "고급 이미지 브랜딩"
    SEASON = "명절·시즌 이벤트"


class Mood(str, Enum):
    """분위기."""

    CLEAN = "깔끔한"
    LUXURY = "고급스러운"
    WARM = "따뜻한"
    TRENDY = "젊고 트렌디한"
    PROFESSIONAL = "믿음 가는 전문적인"
    AFFORDABLE = "저렴하고 실속 있는"


class OutputType(str, Enum):
    """출력 용도."""

    INSTA_FEED = "인스타 피드 4:5"
    INSTA_STORY = "인스타 스토리 9:16"
    NAVER_BLOG = "네이버 블로그 썸네일"
    KAKAO = "카카오톡 채널"
    DANGGEUN = "당근마켓 동네광고"
    EVENT_BANNER = "오픈 이벤트 배너"
    PRICE_TAG = "가격표 이미지"
    REVIEW_CARD = "후기 카드뉴스"


class GenerateResponse(BaseModel):
    """백엔드가 프론트에 돌려주는 결과.

    이미지는 '원본'과 'AI 생성본'을 이름으로 명확히 구분한다.
    (생성 기능 연동 전에는 generated_image_url 이 null)
    """

    session_id: str = Field(..., description="작업 세션 ID (수정요청 때 사용)")
    ad_copy: str = Field(..., description="광고 문구")
    hashtags: list[str] = Field(default_factory=list, description="해시태그")
    original_image_url: str = Field(
        ..., description="사용자가 업로드한 원본 이미지 경로"
    )
    generated_image_url: str | None = Field(
        None, description="AI가 생성한 이미지 경로 (생성 전이면 null)"
    )
    elapsed_time: float = Field(..., description="소요 시간(초)")
