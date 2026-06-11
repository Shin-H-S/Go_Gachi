"""Prompt assembly helpers for the experiments Streamlit console."""

from app_common import ROOT_DIR  # noqa: F401  Ensures backend imports resolve.

from backend.app.core.presets import Preset, PresetDetail
from backend.app.core.prompts import (
    _image_copy_instruction,
    _no_copy_instruction,
    build_user_prompt,
    merge_image_prompt,
)
from backend.app.services.copywriting import AdCopy, build_ad_copy
from backend.app.services.generation_inputs import user_prompt_with_context
from backend.app.services.image_types import TargetSize
from backend.app.services.openai_copy import generate_ad_copy

BASE_LINE = (
    "Edit the uploaded cafe menu photo into a polished promotional food image "
    "for a small local cafe."
)
PRESERVE_LINE = (
    "Preserve the actual menu item identity, shape, ingredients, and serving size. "
    "Do not invent a different product."
)
IMPROVE_LINE = (
    "Improve lighting, color, sharpness, appetizing texture, background cleanliness, "
    "and commercial food styling."
)
MOOD_LINE = "Use a realistic cafe mood with subtle props only when they support the menu item."
NEGATIVE_SPACE_LINE = (
    "Keep the image ready for later ad copy by leaving calm negative space near the edges."
)
COPY_INTRO_LINE = (
    "Create the final image as a complete commercial advertising visual with "
    "integrated typography. Render the supplied ad copy directly inside the image "
    "as part of the design."
)
COPY_LAYOUT_LINE = (
    "Use intentional ad poster layout, strong product hero composition, clean "
    "visual hierarchy, premium lighting, and generous readable space for copy."
)
COPY_ACCURACY_LINE = (
    "Render the supplied Korean text, numbers, punctuation, and prices "
    "as accurately as possible. Do not change prices, menu names, dates, "
    "quantities, or discount numbers. Do not add extra text beyond the "
    "supplied ad copy."
)
COPY_NO_EXTRA_LINE = "Do not add unrelated logos, watermarks, UI, signatures, or brand marks."
LOGO_REF_LINE = (
    "A second reference image contains the shop logo. Use that logo once in "
    "the final advertisement while preserving its shape, wordmark, colors, "
    "and visual identity as much as possible."
)

LOGO_POSITIONS = [
    ("top_left", "왼쪽 상단"),
    ("top_right", "오른쪽 상단"),
    ("bottom_left", "왼쪽 하단"),
    ("bottom_right", "오른쪽 하단"),
]
LOGO_POSITION_LABELS = dict(LOGO_POSITIONS)
COPY_MODE_OPTIONS = [
    ("그대로 사용", "preserve"),
    ("자연스럽게 다듬기", "polish"),
    ("홍보 문구로 바꾸기", "rewrite"),
    ("직접입력", "custom"),
]
COPY_MODE_LABELS = {mode: label for label, mode in COPY_MODE_OPTIONS}
API_SIZES = [
    ("1024x1024 (정사각형)", "1024x1024", 1024, 1024),
    ("1024x1536 (세로형)", "1024x1536", 1024, 1536),
    ("1536x1024 (가로형)", "1536x1024", 1536, 1024),
]
API_SIZE_LABELS = {api: label for label, api, _, _ in API_SIZES}
DIRECT = "직접입력"
REPO_DEFAULT = "레포 기본"

def _logo_place_line(position: str) -> str:
    return (
        f"Place the logo near the {position.replace('_', ' ')} area with "
        "clean margins. Keep it smaller than the main product and do not invent "
        "additional logos or brand marks."
    )


def assemble_system_prompt(cfg: dict, ad_copy: AdCopy | None) -> str:
    parts: list[str] = [BASE_LINE, cfg["channel_hint"], cfg["channel_prompt"], cfg["detail_hint"]]
    parts += [PRESERVE_LINE, IMPROVE_LINE, MOOD_LINE]
    if ad_copy:
        if cfg["copy_instr_custom"]:
            parts += [cfg["copy_instr_custom"], _image_copy_instruction(ad_copy)]
        else:
            parts += [
                COPY_INTRO_LINE,
                COPY_LAYOUT_LINE,
                _image_copy_instruction(ad_copy),
                COPY_ACCURACY_LINE,
                COPY_NO_EXTRA_LINE,
            ]
        if cfg["copy_mode_custom"]:
            parts.append(cfg["copy_mode_custom"])
    else:
        parts += [_no_copy_instruction(allow_logo=cfg["has_logo"]), NEGATIVE_SPACE_LINE]
    if cfg["has_logo"]:
        if cfg["logo_prompt_custom"]:
            parts.append(cfg["logo_prompt_custom"])
        else:
            parts += [LOGO_REF_LINE, _logo_place_line(cfg["logo_position"])]
    return "\n".join(part for part in parts if part)


def assemble_full_prompt(cfg: dict, ad_copy: AdCopy | None) -> str:
    target = TargetSize(width=cfg["target_w"], height=cfg["target_h"])
    detail = PresetDetail(
        id=cfg["detail_id"],
        label=cfg["detail_label"],
        width=cfg["target_w"],
        height=cfg["target_h"],
        api_size=cfg["api_size"],
    )
    ctx = user_prompt_with_context(cfg.get("user_prompt", ""), target, detail, "cover")
    return merge_image_prompt(assemble_system_prompt(cfg, ad_copy), build_user_prompt(ctx))


def preview_ad_copy(cfg: dict) -> AdCopy | None:
    if not cfg["copy_on"]:
        return None
    return build_ad_copy(cfg["copy_text"], "preserve")


def _adcopy_from_result(result: object) -> AdCopy:
    """generate_ad_copy 반환이 AdCopy든 CopyGenerationResult(.copy)든 AdCopy만 꺼낸다."""
    return getattr(result, "copy", result)


async def resolve_ad_copy(cfg: dict, settings) -> AdCopy | None:
    if not cfg["copy_on"]:
        return None
    mode = cfg["copy_mode"]
    if mode == "custom":
        return build_ad_copy(cfg["copy_text"], "preserve")
    preset = Preset(
        id=cfg["channel_id"],
        label=cfg["channel_label"],
        prompt_hint=cfg["channel_hint"],
        channel_prompt=cfg["channel_prompt"],
        details=[],
    )
    # 서비스 문구 생성은 detail 컨텍스트(Detail: label/id)를 포함하므로 동일하게 전달한다.
    detail = PresetDetail(
        id=cfg["detail_id"],
        label=cfg["detail_label"],
        width=cfg["target_w"],
        height=cfg["target_h"],
        api_size=cfg["api_size"],
    )
    try:
        result = await generate_ad_copy(
            settings=settings,
            preset=preset,
            detail=detail,
            user_prompt=cfg.get("user_prompt", ""),
            user_copy=cfg["copy_text"],
            copy_mode=mode,
        )
        return _adcopy_from_result(result)
    except Exception:
        return build_ad_copy(cfg["copy_text"], mode)


# ── 백그라운드 생성 (Streamlit rerun과 독립) ───────────────────────────────
