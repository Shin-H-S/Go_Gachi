"""이미지 편집 프롬프트 조립."""

from backend.app.core.presets import Preset

# 프롬프트 본문/구조가 바뀌면 이 라벨도 올려 캐시 무효화한다. env가 아니라 코드 상수로
# 두는 이유: 프롬프트 변경과 항상 같은 커밋에 들어가야 어긋남이 없어서.
PROMPT_VERSION = "2026-05-28-v1"


def build_prompt(preset: Preset, feedback: str = "") -> str:
    """프리셋과 사용자 피드백을 OpenAI 이미지 편집 지시문으로 만든다."""
    # 사용자가 긴 피드백을 보내도 프롬프트가 과도하게 커지지 않도록 제한한다.
    extra = (feedback or "").strip()[:1200]
    # MVP에서는 텍스트 합성 없이, 메뉴 사진의 상품 정체성과 광고용 품질 개선에 집중한다.
    parts = [
        (
            "Edit the uploaded cafe menu photo into a polished promotional food image "
            "for a small local cafe."
        ),
        preset.prompt_hint,
        (
            "Preserve the actual menu item identity, shape, ingredients, and serving size. "
            "Do not invent a different product."
        ),
        (
            "Improve lighting, color, sharpness, appetizing texture, background cleanliness, "
            "and commercial food styling."
        ),
        "Use a realistic cafe mood with subtle props only when they support the menu item.",
        (
            "Do not add, draw, render, or imitate any text, typography, logo, price tag, "
            "watermark, UI, poster copy, or brand mark."
        ),
        (
            "Keep the image ready for later text overlay by leaving calm negative space "
            "near the edges."
        ),
    ]

    if extra:
        # 프론트에서 받은 수정 요청은 마지막에 붙여 기본 안전 지시를 덮지 않게 한다.
        parts.append(f"User feedback for this revision: {extra}")

    return "\n".join(parts)
