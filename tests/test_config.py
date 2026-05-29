from backend.app.core.presets import get_presets
from backend.app.core.prompts import build_prompt
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
