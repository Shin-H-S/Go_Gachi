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
MOOD_LINE = (
    "Use a warm, inviting cafe mood with soft ambient lighting and consistent color "
    "temperature. Maintain a bright and appetizing atmosphere. Avoid dark, cold, or "
    "low-contrast lighting that diminishes the product's visual appeal."
)
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


def _drift_cfg(preset, detail) -> dict:
    """드리프트 검사용 레포 기본값 cfg."""
    return {
        "channel_id": preset.id,
        "channel_label": preset.label,
        "channel_hint": preset.prompt_hint,
        "channel_prompt": preset.channel_prompt,
        "detail_id": detail.id,
        "detail_label": detail.label,
        "detail_hint": detail.prompt_hint,
        "api_size": detail.api_size,
        "target_w": detail.width,
        "target_h": detail.height,
        "has_logo": False,
        "logo_prompt_custom": "",
        "logo_position": "top_right",
        "copy_on": False,
        "copy_text": "",
        "copy_mode": "preserve",
        "copy_mode_custom": "",
        "copy_instr_custom": "",
        "user_prompt": "",
    }


def prompt_drift_report() -> str | None:
    """콘솔 조립 결과와 백엔드 build_prompt를 비교해 어긋나면 진단 리포트를 만든다.

    어긋남이 없으면 None. 어긋나면 — 어떤 조합이, 어느 줄이, 어떻게 다른지(diff)와
    원인·수정 위치를 담은, AI 어시스턴트에게 그대로 붙여넣을 수 있는 리포트를 돌려준다.
    문자열 비교만 하므로 API 호출·비용은 없다.
    """
    import difflib
    import traceback
    from datetime import datetime

    try:
        from backend.app.core import prompts as backend_prompts
        from backend.app.core.presets import get_presets
        from backend.app.services.generation_inputs import target_size_or_detail

        preset = next(iter(get_presets().values()))
        detail = preset.details[0]
        target = target_size_or_detail(detail=detail, target_width=None, target_height=None)
        base_cfg = _drift_cfg(preset, detail)
        ad = AdCopy(headline="드리프트 검사", subcopy="1,000원", cta="지금", mode="preserve")
        combos = [
            ("기본(문구X 로고X)", base_cfg, None, None, ""),
            ("문구O", {**base_cfg, "copy_on": True}, ad, None, ""),
            ("로고O(top_right)", {**base_cfg, "has_logo": True}, None, "top_right", ""),
            (
                "문구O+로고O+유저 프롬프트",
                {**base_cfg, "copy_on": True, "has_logo": True, "user_prompt": "drift"},
                ad,
                "top_right",
                "drift",
            ),
        ]
        mismatches: list[tuple[str, str]] = []
        for name, cfg, ad_copy, logo_pos, user_prompt in combos:
            ctx = user_prompt_with_context(user_prompt, target, detail, "cover")
            expected = backend_prompts.build_prompt(
                preset, ctx, detail, image_copy=ad_copy, logo_position=logo_pos
            )
            actual = assemble_full_prompt(cfg, ad_copy)
            if actual != expected:
                diff = "\n".join(
                    difflib.unified_diff(
                        actual.splitlines(),
                        expected.splitlines(),
                        fromfile="콘솔 조립 (현재 = 옛 버전)",
                        tofile="백엔드 build_prompt (정답 = 새 버전)",
                        lineterm="",
                        n=2,
                    )
                )
                mismatches.append((name, diff))
        if not mismatches:
            return None

        version = getattr(backend_prompts, "PROMPT_VERSION", "?")
        lines = [
            "=== 프롬프트 드리프트 진단 리포트 (이 블록 전체를 복사해서 전달하세요) ===",
            f"검사 시각: {datetime.now():%Y-%m-%d %H:%M:%S}",
            f"백엔드 PROMPT_VERSION: {version}",
            f"검사 기준: preset={preset.id}, detail={detail.id} / 어긋난 조합 {len(mismatches)}개",
            "",
            "[원인]",
            "backend/app/core/prompts.py의 build_system_prompt 안 고정 문장 또는 조립 순서가",
            "변경되었는데, experiments/app_prompting.py에 복제된 고정 문장 상수",
            "(BASE_LINE, PRESERVE_LINE, IMPROVE_LINE, MOOD_LINE, NEGATIVE_SPACE_LINE,",
            "COPY_INTRO/LAYOUT/ACCURACY/NO_EXTRA_LINE, LOGO_REF_LINE, _logo_place_line)와",
            "assemble_system_prompt의 조립 순서가 아직 옛 버전이기 때문입니다.",
            "",
            "[해결 방법]",
            "아래 diff에서 '+' 줄(백엔드의 새 문장)에 맞게 experiments/app_prompting.py의",
            "해당 상수 또는 assemble_system_prompt의 순서를 수정하면 됩니다.",
            "('-' 줄 = 콘솔이 현재 만들고 있는 옛 문장)",
        ]
        for name, diff in mismatches:
            lines += ["", f"───── 어긋난 조합: {name} ─────", diff]
        return "\n".join(lines)
    except Exception:
        return (
            "=== 프롬프트 드리프트 진단 리포트: 비교 실행 자체가 실패 ===\n"
            "백엔드 함수의 이름·시그니처·모듈 구조가 바뀌었을 가능성이 큽니다.\n"
            "experiments/app_prompting.py가 import하는 백엔드 심볼\n"
            "(build_prompt, _image_copy_instruction, _no_copy_instruction, build_user_prompt,\n"
            " merge_image_prompt, user_prompt_with_context, get_presets)을 점검하세요.\n"
            "아래 오류와 함께 이 블록 전체를 복사해서 전달하면 수정할 수 있습니다.\n\n"
            + traceback.format_exc(limit=4)
        )


# ── 백그라운드 생성 (Streamlit rerun과 독립) ───────────────────────────────
