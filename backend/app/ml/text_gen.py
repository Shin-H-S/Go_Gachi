"""Prompt construction for ad image editing."""

from app.models.schemas import AdGenerationInput, ImageSize


def build_image_edit_prompt(ad_input: AdGenerationInput, size: ImageSize) -> str:
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
