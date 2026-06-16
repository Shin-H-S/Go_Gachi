import os

import pytest

from backend.app.core import config as runtime_config
from backend.app.core.presets import get_presets
from backend.app.core.prompts import (
    PROMPT_VERSION,
    build_prompt,
    build_system_prompt,
    build_user_prompt,
    merge_image_prompt,
)
from backend.app.services.copywriting import AdCopy
from backend.app.services.image_edit import parse_image


def _parse_api_size(api_size: str) -> tuple[int, int]:
    width, height = api_size.split("x", maxsplit=1)
    return int(width), int(height)


def test_presets() -> None:
    presets = get_presets()

    # preset id는 API 요청에 쓰이는 값이라 프론트와 동일하게 유지한다.
    assert set(presets) == {"instagram", "baemin", "daangn"}
    assert all(preset_id.isascii() for preset_id in presets)
    assert presets["instagram"].label == "인스타그램"
    assert presets["baemin"].label == "배달의 민족"
    assert presets["daangn"].label == "당근"
    assert presets["instagram"].channel_prompt
    assert presets["instagram"].default_detail().id == "square_feed"
    assert presets["instagram"].find_detail("story_image").api_size == "1088x1920"
    assert presets["baemin"].find_detail("solid_background") is not None
    assert presets["daangn"].find_detail("menu_image") is not None
    assert presets["daangn"].find_detail("promotion_image") is None


def test_preset_api_sizes_match_generation_constraints() -> None:
    """프리셋 API 규격은 gpt-image-2 제약과 상세 출력 비율에 맞춰 관리한다."""
    for preset in get_presets().values():
        for detail in preset.details:
            api_width, api_height = _parse_api_size(detail.api_size)
            detail_ratio = detail.width / detail.height
            api_ratio = api_width / api_height

            assert api_width % 16 == 0
            assert api_height % 16 == 0
            assert max(api_width, api_height) <= 3840
            assert max(api_width, api_height) / min(api_width, api_height) <= 3
            assert 655_360 <= api_width * api_height <= 8_294_400
            assert abs(api_ratio - detail_ratio) < 0.01


def test_channel_detail_prompt_presets_are_specific() -> None:
    presets = get_presets()

    assert "thumbnail readability" in presets["baemin"].channel_prompt
    assert "nearby shop owner" in presets["daangn"].channel_prompt
    assert "layout balance" in (presets["instagram"].find_detail("story_image").prompt_hint)
    assert "limited offers" in presets["daangn"].find_detail("discount_event").prompt_hint
    assert PROMPT_VERSION == "2026-06-16-v3-v6-crop-safe-centering-policy"


def test_presets_do_not_conflict_with_image_copy_prompting() -> None:
    """프리셋은 채널 스타일만 담당하고, 텍스트 허용/금지는 prompts.py가 조건부로 담당한다."""
    forbidden_phrases = (
        "do not generate text",
        "do not generate people, hands, text",
        "do not generate people, hands, typography",
        "reserve natural empty space for future text placement",
        "preserve layout flexibility for downstream processing",
        "advertising graphics",
    )

    for preset in get_presets().values():
        prompt = f"{preset.prompt_hint} {preset.channel_prompt}".lower()
        for detail in preset.details:
            prompt += f" {detail.prompt_hint.lower()}"

        for phrase in forbidden_phrases:
            assert phrase not in prompt


def test_load_env_uses_only_root_env(monkeypatch, tmp_path) -> None:
    """백엔드도 레포 최상단 .env만 공통 기준으로 읽는다."""
    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()
    (tmp_path / ".env").write_text(
        "APP_ENV=root-env\nOPENAI_TEXT_MODEL=gpt-5\n",
        encoding="utf-8",
    )
    (backend_dir / ".env").write_text(
        "APP_ENV=backend-env\nOPENAI_IMAGE_MODEL=gpt-image-2\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(runtime_config, "ROOT_DIR", tmp_path)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("OPENAI_TEXT_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_IMAGE_MODEL", raising=False)

    runtime_config.load_env()

    assert os.environ["APP_ENV"] == "root-env"
    assert os.environ["OPENAI_TEXT_MODEL"] == "gpt-5"
    assert "OPENAI_IMAGE_MODEL" not in os.environ


def test_database_url_is_required(monkeypatch) -> None:
    """실제 실행 환경에서 DATABASE_URL 누락을 조용한 SQLite 폴백으로 넘기지 않는다."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        runtime_config._database_url_from_env()


def test_sqlite_database_url_requires_explicit_test_flag(monkeypatch) -> None:
    """SQLite URL은 테스트 격리처럼 명시적으로 허용한 경우에만 통과한다."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp/app.db")
    monkeypatch.delenv("ALLOW_SQLITE_DATABASE", raising=False)

    with pytest.raises(RuntimeError, match="SQLite DATABASE_URL"):
        runtime_config._database_url_from_env()


def test_sqlite_database_url_is_allowed_for_isolated_tests(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp/app.db")
    monkeypatch.setenv("ALLOW_SQLITE_DATABASE", "true")

    assert runtime_config._database_url_from_env() == "sqlite:///tmp/app.db"


def test_production_disallows_wildcard_cors() -> None:
    with pytest.raises(RuntimeError, match="CORS_ORIGINS must not include '\\*'"):
        runtime_config._validated_cors_origins("production", ["*"])


def test_cors_origins_trim_trailing_slash() -> None:
    origins = runtime_config._validated_cors_origins(
        "production",
        ["https://gogachi.streamlit.app/"],
    )

    assert origins == ["https://gogachi.streamlit.app"]


def test_production_requires_r2_storage_backend() -> None:
    with pytest.raises(RuntimeError, match="STORAGE_BACKEND must be 'r2' in production"):
        runtime_config._validated_storage_backend("production", "local")


def test_local_allows_local_storage_backend() -> None:
    assert runtime_config._validated_storage_backend("local", "local") == "local"


def test_prompt() -> None:
    preset = get_presets()["instagram"]
    detail = preset.find_detail("story_image")
    prompt = build_prompt(preset, "make it brighter", detail)

    assert "[System instructions]" in prompt
    assert "[User request]" in prompt
    assert "Do not add" in prompt
    assert "text" in prompt.lower()
    assert "make it brighter" in prompt
    assert "Instagram-ready" in prompt
    assert "Instagram Story" in prompt


def test_prompt_builder_splits_system_and_user_prompt() -> None:
    preset = get_presets()["instagram"]
    detail = preset.find_detail("story_image")

    system_prompt = build_system_prompt(preset, detail)
    user_prompt = build_user_prompt("  make it brighter  ")
    merged_prompt = merge_image_prompt(system_prompt, user_prompt)

    assert "Instagram-ready" in system_prompt
    assert "Instagram Story" in system_prompt
    assert "Do not add" in system_prompt
    assert "make it brighter" not in system_prompt
    assert user_prompt == "User request for this generation:\nmake it brighter"
    assert merged_prompt.startswith("[System instructions]")
    assert "[User request]" in merged_prompt
    assert merged_prompt.endswith("make it brighter")


def test_prompt_with_image_copy_asks_image_model_to_render_ad_copy() -> None:
    preset = get_presets()["instagram"]
    detail = preset.find_detail("square_feed")
    image_copy = AdCopy(
        headline="오늘 아메리카노 2,500원",
        subcopy="카페에서 더 맛있게 즐겨보세요.",
        cta=None,
        mode="polish",
    )

    prompt = build_prompt(preset, "따뜻한 광고 이미지", detail, image_copy=image_copy)

    assert "integrated typography" in prompt
    assert "Ad copy to render exactly in the image" in prompt
    assert 'Headline: "오늘 아메리카노 2,500원"' in prompt
    assert "Do not add, draw, render, or imitate any text" not in prompt


def test_prompt_without_copy_rejects_logos_and_brand_marks() -> None:
    preset = get_presets()["instagram"]
    detail = preset.find_detail("square_feed")

    prompt = build_prompt(preset, "깔끔하게", detail)

    assert "provided logo reference" not in prompt
    assert "Do not add, draw, render, suggest, or imitate any text" in prompt
    assert "brand mark" in prompt


def test_empty_user_prompt_keeps_safe_default_instruction() -> None:
    user_prompt = build_user_prompt("")

    assert "No additional user request" in user_prompt
    assert "selected preset" in user_prompt


def test_parse_image_rejects_invalid_base64() -> None:
    try:
        parse_image("data:image/png;base64,abc", 1024)
    except ValueError as exc:
        assert "base64" in str(exc)
    else:
        raise AssertionError("parse_image should reject invalid base64")


def test_parse_image_rejects_non_image_payload() -> None:
    data_url = "data:image/png;base64,aGVsbG8="

    try:
        parse_image(data_url, 1024)
    except ValueError as exc:
        assert "이미지 파일 형식" in str(exc)
    else:
        raise AssertionError("parse_image should reject non-image bytes")


def test_parse_image_rejects_mismatched_mime_type() -> None:
    jpg_declared_png_bytes = (
        "data:image/jpeg;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhg"
        "GAWjR9awAAAABJRU5ErkJggg=="
    )

    try:
        parse_image(jpg_declared_png_bytes, 1024)
    except ValueError as exc:
        assert "MIME 타입" in str(exc)
    else:
        raise AssertionError("parse_image should reject mismatched MIME type")
