import asyncio
import base64
import re
from pathlib import Path

import pytest
from sqlalchemy import func, select

from backend.app.core.presets import default_preset
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.db.models import ApiUsage, Generation
from backend.app.services import generation_service, image_edit
from tests.api.helpers import TINY_PNG_B64, TINY_PNG_DATA_URL, client, force_openai_mode


def test_openai_cache_hit_on_repeated_input(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs: object) -> str:
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    real_settings = force_openai_mode(monkeypatch)
    preset = default_preset()

    result1 = asyncio.run(
        image_edit.edit_image(
            image_data_url=TINY_PNG_DATA_URL,
            preset=preset,
            user_prompt="밝게 해주세요",
            settings=real_settings,
        )
    )
    result2 = asyncio.run(
        image_edit.edit_image(
            image_data_url=TINY_PNG_DATA_URL,
            preset=preset,
            user_prompt="밝게 해주세요",
            settings=real_settings,
        )
    )

    assert result1["provider"] == "openai"
    assert result1["image_url"].startswith("/outputs/")
    assert result2["provider"] == "openai"
    assert result2["image_url"] == result1["image_url"]
    assert result2["note"] == "캐시된 결과 재사용"

    async def _db_state() -> tuple[list[object], int, int]:
        async with async_session_scope() as db:
            status_result = await db.execute(
                select(
                    Generation.status,
                    Generation.original_path,
                    Generation.output_path,
                ).order_by(Generation.id)
            )
            cached_usage_result = await db.execute(
                select(func.count()).select_from(ApiUsage).where(ApiUsage.cached.is_(True))
            )
            total_usage_result = await db.execute(select(func.count()).select_from(ApiUsage))
            return (
                list(status_result.all()),
                int(cached_usage_result.scalar_one()),
                int(total_usage_result.scalar_one()),
            )

    generation_rows, cached_usage_count, total_usage_count = asyncio.run(_db_state())
    assert [row.status for row in generation_rows] == ["success", "cached"]
    assert generation_rows[1].original_path == generation_rows[0].original_path
    assert Path(generation_rows[0].original_path).exists()
    assert Path(generation_rows[0].output_path).exists()
    assert re.fullmatch(r"\d{8}_\d{6}_[0-9a-f]{6}\.png", Path(generation_rows[0].output_path).name)
    assert Path(generation_rows[0].original_path).read_bytes() == base64.b64decode(TINY_PNG_B64)
    assert cached_usage_count == 1
    assert total_usage_count == 2


def test_generate_stores_logo_metadata_without_overlay(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs: object) -> str:
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "bright mood",
            "userCopy": "lemonade menu copy",
            "logoDataUrl": TINY_PNG_DATA_URL,
            "logoPosition": "bottom_right",
        },
    )

    assert response.status_code == 200

    async def _db_state() -> tuple[str | None, bool, str | None, str, str | None]:
        async with async_session_scope() as db:
            result = await db.execute(select(Generation))
            generation = result.scalar_one()
            return (
                generation.user_copy,
                generation.has_logo,
                generation.logo_position,
                generation.instruction_hash,
                generation.logo_storage_key,
            )

    user_copy, has_logo, logo_position, instruction_hash, logo_storage_key = asyncio.run(
        _db_state()
    )
    assert user_copy is None
    assert has_logo is True
    assert logo_position == "bottom_right"
    assert instruction_hash != crud.instruction_sha256("bright mood")
    assert logo_storage_key is None


def test_generate_stores_rendered_user_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs: object) -> str:
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    expected_copy = (
        "오늘 놓치기 아까운 딸기 케이크 6,500원\n"
        "카페에서 즐기는 신선한 메뉴를 더 맛있게 전해드려요.\n"
        "지금 방문해보세요"
    )
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "bright mood",
            "userCopy": "딸기 케이크 6500원",
            "copyMode": "rewrite",
            "textOverlayEnabled": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["copy"] == {
        "headline": "오늘 놓치기 아까운 딸기 케이크 6,500원",
        "subcopy": "카페에서 즐기는 신선한 메뉴를 더 맛있게 전해드려요.",
        "cta": "지금 방문해보세요",
        "copyMode": "rewrite",
    }

    async def _saved_user_copy() -> str | None:
        async with async_session_scope() as db:
            result = await db.execute(select(Generation.user_copy))
            return result.scalar_one()

    assert asyncio.run(_saved_user_copy()) == expected_copy


def test_generate_cache_hit_stores_rendered_user_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs: object) -> str:
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    payload = {
        "imageDataUrl": TINY_PNG_DATA_URL,
        "presetId": "instagram",
        "detailType": "square_feed",
        "userPrompt": "bright mood",
        "userCopy": "라떼 4500원",
        "copyMode": "polish",
        "textOverlayEnabled": True,
    }
    first = client.post("/api/generate", json=payload)
    second = client.post("/api/generate", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["note"] == "캐시된 결과 재사용"

    async def _db_state() -> list[tuple[str, str | None]]:
        async with async_session_scope() as db:
            result = await db.execute(
                select(Generation.status, Generation.user_copy).order_by(Generation.id)
            )
            return list(result.all())

    rows = asyncio.run(_db_state())
    assert rows == [
        ("success", "라떼 4,500원\n카페에서 더 맛있게 즐겨보세요."),
        ("cached", "라떼 4,500원\n카페에서 더 맛있게 즐겨보세요."),
    ]


def test_generate_stores_blank_user_copy_as_none(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs: object) -> str:
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "bright mood",
            "userCopy": "   ",
        },
    )

    assert response.status_code == 200

    async def _saved_user_copy() -> str | None:
        async with async_session_scope() as db:
            result = await db.execute(select(Generation.user_copy))
            return result.scalar_one()

    assert asyncio.run(_saved_user_copy()) is None


def test_generate_ignores_user_copy_when_text_overlay_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_call(**kwargs: object) -> str:
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "bright mood",
            "userCopy": "이미지에 합성하지 않는 문구",
            "textOverlayEnabled": False,
        },
    )

    assert response.status_code == 200

    async def _saved_user_copy() -> str | None:
        async with async_session_scope() as db:
            result = await db.execute(select(Generation.user_copy))
            return result.scalar_one()

    assert asyncio.run(_saved_user_copy()) is None
