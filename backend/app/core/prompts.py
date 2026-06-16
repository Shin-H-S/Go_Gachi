"""이미지 편집 프롬프트 조립."""

from backend.app.core.presets import Preset, PresetDetail
from backend.app.services.copywriting import AdCopy

# 프롬프트 본문/구조가 바뀌면 이 라벨도 올려 캐시 무효화한다. env가 아니라 코드 상수로
# 두는 이유: 프롬프트 변경과 항상 같은 커밋에 들어가야 어긋남이 없어서.
PROMPT_VERSION = "2026-06-16-v3-v7-daangn-discount-visual-refinement"


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
    if image_copy and _should_render_image_copy(preset, detail):
        parts.extend(
            [
                _image_copy_layout_instruction(preset, detail),
                _image_copy_instruction(image_copy),
                _image_copy_style_instruction(preset, detail),
                "Do not add unrelated logos, watermarks, UI, signatures, or brand marks.",
            ]
        )

    elif image_copy:
        parts.extend(
            [
                _baemin_ignore_image_copy_instruction(),
                _no_copy_instruction(),
            ]
        )

    else:
        parts.extend([
            _no_copy_instruction(),
            (
                "Do not render, add, draw, suggest, or imitate any text, typography, "
                "pricing, numbers, labels, or brand information anywhere in the image. "
                "The image must be completely text-free and ready for later ad copy placement. "
                "Preserve visually comfortable negative space only when it does not conflict "
                "with the selected preset and detail composition policy. "
                "Follow preset and detail positioning rules with higher priority "
                "than future text placement."
            ),
        ])

    return "\n".join(parts)


def _should_render_image_copy(preset: Preset, detail: PresetDetail | None) -> bool:
    """채널/상세 정책에 따라 이미지 내 광고 문구 렌더링 여부를 결정한다."""
    if preset.id == "baemin":
        return False

    if preset.id == "instagram":
        return True

    if preset.id == "daangn":
        return detail is not None and detail.id == "discount_event"

    return False


def _image_copy_layout_instruction(preset: Preset, detail: PresetDetail | None) -> str:
    """광고 문구 포함 시 채널 정책에 맞는 레이아웃 지시문."""
    base = (
        "Create the final image as a complete commercial advertising visual with "
        "integrated typography. Render the supplied ad copy directly inside the image "
        "as part of the design. "
        "Place the product as the dominant focal point while preserving full product visibility. "
        "Use clear visual hierarchy: product > headline > subcopy > CTA. "
        "Leave generous whitespace around text for readability. "
    )

    if preset.id == "instagram":
        return base + (
            "For Instagram, allow clean Korean typography naturally integrated into the "
            "SNS-style promotional composition. Position the product and text so they form "
            "a balanced advertising layout without cropping or reducing product clarity."
        )

    if preset.id == "daangn" and detail and detail.id == "discount_event":
        return base + (
            "For Danggeun discount_event, allow readable local promotional typography "
            "only because this selected detail is an event image. Keep the mood approachable, "
            "local, and practical rather than overly polished."
        )

    return base


def _image_copy_style_instruction(preset: Preset, detail: PresetDetail | None) -> str:
    """광고 문구 렌더링 스타일과 채널별 우선 정책."""
    base = (
        "Render headline in a bold, punchy sans-serif or display font. "
        "Render subcopy in a clean, legible sans-serif. "
        "Render CTA clearly and compactly. "
        "Ensure adequate contrast for readability on the background. "
        "Render the supplied Korean text, numbers, punctuation, and prices "
        "as accurately as possible. "
        "Do not change prices, menu names, dates, quantities, "
        "or discount numbers. "
        "Do not add extra text beyond the supplied ad copy."
    )

    if preset.id == "daangn" and detail and detail.id == "discount_event":
        return base + (
            "For Danggeun discount_event, the CTA color policy has priority: "
            "apply Danggeun brand orange (#F7863B) ONLY to CTA button backgrounds. "
            "Do not apply #F7863B to headlines, subcopy, event text, decorations, "
            "background tint, props, lighting, or overall color grading. "
            "Headline and subcopy colors should be selected adaptively for readability."
        )

    return base


def _baemin_ignore_image_copy_instruction() -> str:
    """배민 채널은 광고 문구가 있어도 이미지 내 텍스트 렌더링을 금지한다."""
    return (
        "Although ad copy was supplied internally, this Baemin preset "
        "must remain text-free. "
        "Do not render the supplied headline, subcopy, CTA, "
        "or any other typography inside the image. "
        "Follow the Baemin channel policy: create a clean product-only image optimized for "
        "delivery-app thumbnail readability and ordering decisions."
    )


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
    """광고 문구 미포함 시 텍스트와 타이포그래피 절대 금지 규칙."""
    return (
        "Do not add, draw, render, suggest, or imitate any text, typography, "
        "price tags, logos, watermarks, UI elements, poster copy, brand marks, "
        "or any form of written or visual communication. "
        "The image must be completely text-free and logo-free. "
        "Focus only on the product, lighting, composition, and styling."
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
