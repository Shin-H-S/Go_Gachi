"""광고 이미지 편집용 프롬프트(지시문) 생성.

사용자가 고른 값(업종·분위기·게시위치 등)을 OpenAI 가 알아들을 영어 지시문 한 덩어리로
조립한다. 지금은 규칙 기반이며, 이후 카피 생성 모델을 붙여도 이 함수만 바꾸면 된다.
"""

from app.models.schemas import AdGenerationInput, ImageSize


def ad_prompt(ad_input: AdGenerationInput, size: ImageSize) -> str:
    """광고 입력값을 OpenAI 에 보낼 프롬프트 문자열로 조립한다.

    Args:
        ad_input: 검증된 광고 생성 입력(업종·분위기·목적 등).
        size: 최종 캔버스 크기(프롬프트에 명시해 구도 잡기에 참고시킴).
    Returns:
        여러 줄로 된 영어 지시문. 선택 입력(상호명 등)은 값이 있을 때만 포함된다.
    """
    # 현재는 규칙 기반 프롬프트를 만들고, 이후 카피 생성 모델을 붙여도 이 함수만 교체하면 됩니다.
    details = [
        f"Industry: {ad_input.industry}",
        f"Mood: {ad_input.mood}",
        f"Ad type: {ad_input.ad_type}",
        f"Objective: {ad_input.objective}",
        f"Placement: {ad_input.placement.value}",
        f"Final canvas: {size.width}x{size.height}",
    ]
    optional_details = {
        "Brand name": ad_input.brand_name,
        "Target audience": ad_input.target_audience,
        "Key message": ad_input.key_message,
        "Offer": ad_input.offer,
    }
    details.extend(
        f"{key}: {value}" for key, value in optional_details.items() if value
    )

    return "\n".join(
        [
            "Edit and recompose the uploaded source image into a polished Korean small-business advertisement.",
            "Keep the recognizable subject or product from the original image, but improve composition, lighting, background, and visual hierarchy.",
            "Create enough clean negative space for future copy overlays. Do not add readable text, logos, QR codes, watermarks, or fake UI.",
            "Make the result suitable for the requested industry, mood, ad type, business objective, and publishing placement.",
            "Use a commercial, trustworthy, high-quality style rather than a generic stock-photo look.",
            "",
            "Creative brief:",
            *details,
        ]
    )
