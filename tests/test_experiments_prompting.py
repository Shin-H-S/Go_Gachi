import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = ROOT_DIR / "experiments"
if str(EXPERIMENTS_DIR) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_DIR))

import app_prompting  # noqa: E402
from app_prompting import assemble_full_prompt, resolve_ad_copy  # noqa: E402
from runner import build_case_prompt  # noqa: E402

from backend.app.core.presets import Preset, PresetDetail, get_presets  # noqa: E402
from backend.app.core.prompts import build_prompt  # noqa: E402
from backend.app.services.copywriting import AdCopy  # noqa: E402
from backend.app.services.generation_inputs import user_prompt_with_context  # noqa: E402
from backend.app.services.image_types import TargetSize  # noqa: E402
from frontend.services.prompting import (  # noqa: E402
    build_user_prompt as build_frontend_user_prompt,
)


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
            frontend_user_prompt = build_frontend_user_prompt("밝게", detail.label)
            context_prompt = user_prompt_with_context(
                frontend_user_prompt,
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


def test_experiments_runner_uses_frontend_user_prompt_shape() -> None:
    preset = get_presets()["instagram"]
    detail = preset.find_detail("square_feed")
    assert detail is not None

    prompt, _meta = build_case_prompt(
        {
            "id": "frontend-shape",
            "preset": preset.id,
            "detail": detail.id,
            "user_prompt": "더 밝고 깔끔하게",
        },
        preset,
        detail,
    )
    frontend_user_prompt = build_frontend_user_prompt("더 밝고 깔끔하게", detail.label)
    context_prompt = user_prompt_with_context(
        frontend_user_prompt,
        TargetSize(width=detail.width, height=detail.height),
        detail,
        "cover",
    )

    assert prompt == build_prompt(preset, context_prompt, detail)


def test_custom_copy_mode_prompt_replaces_copy_processing_prompt_only() -> None:
    preset = get_presets()["instagram"]
    detail = preset.find_detail("square_feed")
    assert detail is not None

    cfg = {
        **_cfg(preset, detail, user_prompt="brighter mood"),
        "copy_on": True,
        "copy_text": "Original copy",
        "copy_mode": "custom",
        "copy_mode_custom": "CUSTOM_COPY_PROCESSING_PROMPT",
    }
    prompt = assemble_full_prompt(
        cfg,
        AdCopy(headline="Rendered headline", subcopy=None, cta=None, mode="preserve"),
    )

    assert "CUSTOM_COPY_PROCESSING_PROMPT" not in prompt
    assert 'Headline: "Rendered headline"' in prompt


def test_custom_copy_mode_forwards_replacement_prompt_to_copy_generation(monkeypatch) -> None:
    preset = get_presets()["instagram"]
    detail = preset.find_detail("square_feed")
    assert detail is not None
    captured: dict[str, object] = {}

    async def fake_generate_ad_copy(**kwargs: object) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace(
            copy=AdCopy(
                headline="Custom generated headline",
                subcopy=None,
                cta=None,
                mode="preserve",
            )
        )

    monkeypatch.setattr(app_prompting, "generate_ad_copy", fake_generate_ad_copy)
    cfg = {
        **_cfg(preset, detail, user_prompt="brighter mood"),
        "copy_on": True,
        "copy_text": "Original copy",
        "copy_mode": "custom",
        "copy_mode_custom": "CUSTOM_COPY_PROCESSING_PROMPT",
    }

    ad_copy = asyncio.run(
        resolve_ad_copy(
            cfg,
            SimpleNamespace(image_provider="openai", openai_api_key="test-key"),
        )
    )

    assert ad_copy.headline == "Custom generated headline"
    assert captured["system_prompt_override"] == "CUSTOM_COPY_PROCESSING_PROMPT"
    assert captured["copy_mode"] == "preserve"
