import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = ROOT_DIR / "experiments"
if str(EXPERIMENTS_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_DIR))

from app_prompting import assemble_full_prompt  # noqa: E402

from backend.app.core.presets import Preset, PresetDetail, get_presets  # noqa: E402
from backend.app.core.prompts import build_prompt  # noqa: E402
from backend.app.services.copywriting import AdCopy  # noqa: E402
from backend.app.services.generation_inputs import user_prompt_with_context  # noqa: E402
from backend.app.services.image_types import TargetSize  # noqa: E402


def _cfg(preset: Preset, detail: PresetDetail, *, user_prompt: str) -> dict:
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
        "copy_text": "",
        "copy_mode": "preserve",
        "copy_mode_custom": "",
        "copy_instr_custom": "",
        "user_prompt": user_prompt,
    }


def test_experiments_default_prompts_are_built_by_backend_prompt_pipeline() -> None:
    ad_copy = AdCopy(
        headline="테스트 헤드라인",
        subcopy="1,000원",
        cta="지금",
        mode="preserve",
    )
    mismatches: list[str] = []

    for preset in get_presets().values():
        for detail in preset.details:
            target_size = TargetSize(width=detail.width, height=detail.height)
            context_prompt = user_prompt_with_context(
                "밝게",
                target_size,
                detail,
                "cover",
            )
            cfg = _cfg(preset, detail, user_prompt="밝게")

            for image_copy in (None, ad_copy):
                actual = assemble_full_prompt(cfg, image_copy)
                expected = build_prompt(
                    preset,
                    context_prompt,
                    detail,
                    image_copy=image_copy,
                )
                if actual != expected:
                    suffix = "copy" if image_copy else "no-copy"
                    mismatches.append(f"{preset.id}/{detail.id}/{suffix}")

    assert mismatches == []
