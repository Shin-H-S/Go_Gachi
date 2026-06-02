import os

import pytest

from backend.app.core import config as runtime_config
from backend.app.core.presets import get_presets
from backend.app.core.prompts import PROMPT_VERSION, build_prompt
from backend.app.services.image_edit import parse_image


def test_presets() -> None:
    presets = get_presets()

    # preset id는 API 요청에 쓰이는 값이라 프론트와 동일하게 유지한다.
    assert set(presets) == {"instagram_square", "baemin_notice", "daangn_post"}
    assert all(preset_id.isascii() for preset_id in presets)
    assert presets["instagram_square"].width == 1080
    assert presets["instagram_square"].label == "인스타그램"
    assert presets["baemin_notice"].label == "배달의 민족"
    assert presets["daangn_post"].label == "당근"
    assert presets["instagram_square"].channel_prompt
    assert presets["instagram_square"].find_detail("story_image") is not None
    assert presets["baemin_notice"].find_detail("solid_background") is not None
    assert presets["daangn_post"].find_detail("promotion_image") is not None


def test_channel_detail_prompt_presets_are_specific() -> None:
    presets = get_presets()

    assert "thumbnail readability" in presets["baemin_notice"].channel_prompt
    assert "nearby shop owner" in presets["daangn_post"].channel_prompt
    assert "story stickers or text" in (
        presets["instagram_square"].find_detail("story_image").prompt_hint
    )
    assert "seasonal offer" in presets["daangn_post"].find_detail("discount_event").prompt_hint
    assert PROMPT_VERSION == "2026-05-30-v3-channel-detail-presets"


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


def test_prompt() -> None:
    preset = get_presets()["instagram_square"]
    detail = preset.find_detail("story_image")
    prompt = build_prompt(preset, "make it brighter", detail)

    assert "Do not add" in prompt
    assert "text" in prompt.lower()
    assert "make it brighter" in prompt
    assert "Instagram-ready" in prompt
    assert "Instagram Story" in prompt


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
