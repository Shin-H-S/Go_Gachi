import asyncio

import pytest
from sqlalchemy import select

from backend.app.db.database import async_session_scope
from backend.app.db.models import ApiUsage, Generation
from backend.app.services import generation_service, openai_copy
from backend.app.services.copywriting import AdCopy
from backend.app.services.openai_copy import CopyGenerationResult
from tests.api.helpers import (
    TINY_PNG_B64,
    TINY_PNG_DATA_URL,
    client,
    force_openai_mode,
    image_size_from_data_url,
)


def test_generate_hides_prompt_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

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

    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        captured_call["api_size"] = kwargs["api_size"]
        return TINY_PNG_B64, {}

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
    captured_call: dict[str, object] = {}

    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        captured_call.update(kwargs)
        return TINY_PNG_B64, {}

    async def _fake_copy(**kwargs: object) -> CopyGenerationResult:
        return CopyGenerationResult(
            copy=AdCopy(
                headline="오늘 아메리카노 2,500원",
                subcopy="카페에서 더 맛있게 즐겨보세요.",
                cta=None,
                mode="polish",
            )
        )

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    monkeypatch.setattr(openai_copy, "call_openai_copy", _fake_copy)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "V3 userPrompt 문구",
            "userCopy": "오늘 아메리카노 2500원",
            "copyMode": "polish",
            "adCopyEnabled": True,
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
    assert "Ad copy to render exactly in the image" in body["prompt"]
    assert 'Headline: "오늘 아메리카노 2,500원"' in body["prompt"]
    assert body["copy"] == {
        "headline": "오늘 아메리카노 2,500원",
        "subcopy": "카페에서 더 맛있게 즐겨보세요.",
        "cta": None,
        "copyMode": "polish",
    }
    assert body["logo"] == {"used": True, "position": "top_right"}
    assert body["revision"] is None
    assert "A second reference image contains the shop logo" in body["prompt"]
    assert "top right" in body["prompt"]
    assert len(captured_call["reference_images"]) == 1

    async def _saved_text_model() -> str | None:
        async with async_session_scope() as db:
            result = await db.execute(select(Generation.text_model))
            return result.scalar_one()

    assert asyncio.run(_saved_text_model()) == "gpt-5"


def test_generate_uses_default_copy_when_user_copy_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

    async def _fake_copy(**kwargs: object) -> CopyGenerationResult:
        return CopyGenerationResult(
            copy=AdCopy(
                headline="오늘도 기분 좋은 카페 한 잔",
                subcopy="가볍게 들르기 좋은 동네 카페 메뉴를 만나보세요.",
                cta="지금 매장에서 확인해보세요",
                mode="preserve",
            )
        )

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    monkeypatch.setattr(openai_copy, "call_openai_copy", _fake_copy)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "따뜻한 카페 분위기로 만들어줘",
            "userCopy": "",
            "copyMode": "preserve",
            "adCopyEnabled": True,
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert "따뜻한 카페 분위기로 만들어줘" in body["prompt"]
    assert 'Headline: "오늘도 기분 좋은 카페 한 잔"' in body["prompt"]
    assert body["copy"] == {
        "headline": "오늘도 기분 좋은 카페 한 잔",
        "subcopy": "가볍게 들르기 좋은 동네 카페 메뉴를 만나보세요.",
        "cta": "지금 매장에서 확인해보세요",
        "copyMode": "preserve",
    }


def test_generate_exposes_prompt_in_local(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

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


def test_generate_records_image_usage_cost(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {"input_tokens": 1000, "output_tokens": 2000}

    async def _saved_cost() -> float:
        async with async_session_scope() as db:
            result = await db.execute(select(ApiUsage.cost_usd))
            return float(result.scalar_one())

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "token usage cost test",
        },
    )

    assert response.status_code == 200
    assert asyncio.run(_saved_cost()) == 0.068


def test_generate_records_text_usage_cost(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

    async def _fake_copy(**kwargs: object) -> CopyGenerationResult:
        return CopyGenerationResult(
            copy=AdCopy(
                headline="신메뉴 출시",
                subcopy="오늘만 특별한 커피를 만나보세요",
                cta=None,
                mode="rewrite",
            ),
            usage={"input_tokens": 1000, "output_tokens": 2000},
            used_openai=True,
        )

    async def _saved_text_cost() -> float:
        async with async_session_scope() as db:
            result = await db.execute(
                select(ApiUsage.cost_usd).where(ApiUsage.operation == "text_generation")
            )
            return float(result.scalar_one())

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    monkeypatch.setattr(openai_copy, "call_openai_copy", _fake_copy)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "text usage cost test",
            "copyMode": "rewrite",
            "adCopyEnabled": True,
        },
    )

    assert response.status_code == 200
    assert asyncio.run(_saved_text_cost()) == 0.02125
