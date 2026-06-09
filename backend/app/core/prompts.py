"""이미지 편집 프롬프트 조립."""

from backend.app.core.presets import Preset, PresetDetail

# 프롬프트 본문/구조가 바뀌면 이 라벨도 올려 캐시 무효화한다. env가 아니라 코드 상수로
# 두는 이유: 프롬프트 변경과 항상 같은 커밋에 들어가야 어긋남이 없어서.
PROMPT_VERSION = "2026-06-06-v1-system-user-prompt-builder"


def _clean_parts(parts: list[str]) -> list[str]:
    """빈 프롬프트 조각을 제거해 최종 조립 결과를 안정적으로 만든다."""
    return [part for part in parts if part]


def build_system_prompt(
    preset: Preset,
    detail: PresetDetail | None = None,
) -> str:
    """프리셋 기반의 고정 규칙을 system 성격 프롬프트로 만든다."""
    # MVP에서는 텍스트 합성 없이, 메뉴 사진의 상품 정체성과 광고용 품질 개선에 집중한다.
    parts = _clean_parts(
        [
            (
                "Edit the uploaded cafe menu photo into a polished promotional food image "
                "for a small local cafe."
            ),
            preset.prompt_hint,
            preset.channel_prompt,
            detail.prompt_hint if detail else "",
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
    )

    return "\n".join(parts)


def build_user_prompt(user_prompt: str = "") -> str:
    """프론트에서 받은 사용자 요청을 user 성격 프롬프트로 만든다."""
    # 사용자가 긴 요청을 보내도 프롬프트가 과도하게 커지지 않도록 제한한다.
    extra = (user_prompt or "").strip()[:1200]
    if not extra:
        return (
            "No additional user request was provided. Follow the system instructions "
            "and selected preset."
        )
    return f"User request for this generation:\n{extra}"


def merge_image_prompt(system_prompt: str, user_prompt: str) -> str:
    """Images API용 단일 prompt로 합친다.

    현재 Images API는 system/user 역할 필드를 따로 받지 않으므로, 내부에서 분리한
    프롬프트를 명시적인 섹션으로 합쳐 전달한다. 추후 Responses API 전환 시 이 함수
    대신 각 프롬프트를 역할 메시지로 보내면 된다.
    """
    parts = _clean_parts(
        [
            "[System instructions]",
            system_prompt.strip(),
            "[User request]",
            user_prompt.strip(),
        ]
    )
    return "\n".join(parts)


def build_prompt(
    preset: Preset,
    user_prompt: str = "",
    detail: PresetDetail | None = None,
) -> str:
    """프리셋 규칙과 사용자 요청을 현재 Images API용 단일 지시문으로 만든다."""
    system_prompt = build_system_prompt(preset, detail)
    user_prompt_text = build_user_prompt(user_prompt)
    return merge_image_prompt(system_prompt, user_prompt_text)
