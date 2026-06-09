import pytest

from backend.app.services import generation_service
from tests.api.helpers import (
    TINY_PNG_B64,
    TINY_PNG_DATA_URL,
    client,
    force_openai_mode,
    image_size_from_data_url,
)


def test_generate_hides_prompt_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    real_settings = force_openai_mode(monkeypatch)
    monkeypatch.setattr(real_settings, "app_env", "production")

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "userPrompt": ""},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["provider"] == "openai"
    assert body["prompt"] is None


def test_generate_openai_result_matches_target_size(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_call: dict[str, str] = {}

    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        captured_call["api_size"] = kwargs["api_size"]
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "story_image",
            "userPrompt": "밝게",
            "targetWidth": 1080,
            "targetHeight": 1920,
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["provider"] == "openai"
    assert body["imageUrl"].startswith("/outputs/")
    assert body["imageUrl"].endswith(".png")
    assert image_size_from_data_url(body["imageDataUrl"]) == (1080, 1920)
    assert "1080x1920" in body["prompt"]
    assert captured_call["api_size"] == "1024x1536"


def test_generate_uses_user_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "V3 userPrompt 문구",
            "copyMode": "polish",
            "textOverlayEnabled": True,
            "logoDataUrl": TINY_PNG_DATA_URL,
            "logoPosition": "top_right",
            "parentRequestId": "parent-generation-id",
            "targetWidth": 1080,
            "targetHeight": 1080,
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert "V3 userPrompt 문구" in body["prompt"]
    assert body["copy"] == {
        "headline": "V3 userPrompt 문구",
        "subcopy": "카페에서 더 맛있게 즐겨보세요.",
        "cta": None,
        "copyMode": "polish",
    }
    assert body["logo"] is None
    assert body["revision"] is None


def test_generate_exposes_prompt_in_local(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    real_settings = force_openai_mode(monkeypatch)
    assert real_settings.app_env != "production"

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "userPrompt": ""},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["provider"] == "openai"
    assert body["prompt"] is not None
    assert "cafe" in body["prompt"].lower()
