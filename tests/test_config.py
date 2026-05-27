from backend.app.core.presets import get_presets
from backend.app.core.prompts import build_prompt
from backend.app.services.image_edit import parse_image


def test_presets() -> None:
    presets = get_presets()

    assert "instagram_square" in presets
    assert presets["instagram_square"].width == 1080


def test_prompt() -> None:
    preset = get_presets()["instagram_square"]
    prompt = build_prompt(preset, "make it brighter")

    assert "Do not add" in prompt
    assert "text" in prompt.lower()
    assert "make it brighter" in prompt


def test_parse_image_rejects_invalid_base64() -> None:
    try:
        parse_image("data:image/png;base64,abc", 1024)
    except ValueError as exc:
        assert "base64" in str(exc)
    else:
        raise AssertionError("parse_image should reject invalid base64")
