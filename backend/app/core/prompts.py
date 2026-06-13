"""이미지 편집 프롬프트 조립."""

from backend.app.core.presets import Preset, PresetDetail
from backend.app.services.copywriting import AdCopy

# 프롬프트 본문/구조가 바뀌면 이 라벨도 올려 캐시 무효화한다. env가 아니라 코드 상수로
# 두는 이유: 프롬프트 변경과 항상 같은 커밋에 들어가야 어긋남이 없어서.
PROMPT_VERSION = "2026-06-12-v4-instagram-ad-enhancement"


def _clean_parts(parts: list[str]) -> list[str]:
    """빈 프롬프트 조각을 제거해 최종 조립 결과를 안정적으로 만든다."""
    return [part for part in parts if part]


def build_system_prompt(
    preset: Preset,
    detail: PresetDetail | None = None,
    image_copy: AdCopy | None = None,
) -> str:
    """프리셋 기반의 고정 규칙을 system 성격 프롬프트로 만든다."""
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
            # 분위기 제약 없으면 어둡게 해석하는 경우가 있어 밝은 느낌으로 명시한다.
            (
                "Use a warm, inviting cafe mood with soft ambient lighting and "
                "consistent color temperature. Maintain a bright and appetizing "
                "atmosphere. Avoid dark, cold, or low-contrast lighting that "
                "diminishes the product's visual appeal."
            ),
        ]
    )
    if image_copy:
        parts.extend(
            [
                (
                    "Create the final image as a complete commercial advertising visual with "
                    "integrated typography. Render the supplied ad copy directly inside the image "
                    "as part of the design."
                ),
                (
                    "Use intentional ad poster layout, strong product hero composition, clean "
                    "visual hierarchy, premium lighting, and generous readable space for copy."
                ),
                _image_copy_instruction(image_copy),
                (
                    "Render the supplied Korean text, numbers, punctuation, and prices "
                    "as accurately as possible. Do not change prices, menu names, dates, "
                    "quantities, or discount numbers. Do not add extra text beyond the "
                    "supplied ad copy."
                ),
                "Do not add unrelated logos, watermarks, UI, signatures, or brand marks.",
            ]
        )
    else:
        parts.extend(
            [
                _no_copy_instruction(),
                (
                    "Keep the image ready for later ad copy by leaving calm negative space "
                    "near the edges."
                ),
            ]
        )

    return "\n".join(parts)


def _image_copy_instruction(image_copy: AdCopy) -> str:
    """이미지 모델이 직접 넣을 광고 문구를 명시한다."""
    lines = ["Ad copy to render exactly in the image:"]
    if image_copy.headline:
        lines.append(f'Headline: "{image_copy.headline}"')
    if image_copy.subcopy:
        lines.append(f'Subcopy: "{image_copy.subcopy}"')
    if image_copy.cta:
        lines.append(f'CTA: "{image_copy.cta}"')
    return "\n".join(lines)


def _no_copy_instruction() -> str:
    """광고 문구를 쓰지 않을 때 금지할 요소를 만든다."""
    return (
        "Do not add, draw, render, or imitate any text, typography, logo, price tag, "
        "watermark, UI, poster copy, or brand mark."
    )


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
    image_copy: AdCopy | None = None,
) -> str:
    """프리셋 규칙과 사용자 요청을 현재 Images API용 단일 지시문으로 만든다."""
    system_prompt = build_system_prompt(preset, detail, image_copy)
    user_prompt_text = build_user_prompt(user_prompt)
    return merge_image_prompt(system_prompt, user_prompt_text)
