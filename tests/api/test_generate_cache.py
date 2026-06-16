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
from backend.app.services import generation_service, image_edit, openai_copy
from backend.app.services.copywriting import AdCopy
from backend.app.services.openai_copy import CopyGenerationResult
from tests.api.helpers import TINY_PNG_B64, TINY_PNG_DATA_URL, client, force_openai_mode


def test_openai_cache_hit_on_repeated_input(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

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


def test_cache_hit_falls_back_to_older_existing_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    real_settings = force_openai_mode(monkeypatch)
    preset = default_preset()

    first = asyncio.run(
        image_edit.edit_image(
            image_data_url=TINY_PNG_DATA_URL,
            preset=preset,
            user_prompt="same prompt",
            settings=real_settings,
        )
    )

    async def _add_newer_missing_cache() -> None:
        async with async_session_scope() as db:
            result = await db.execute(select(Generation).where(Generation.status == "success"))
            row = result.scalar_one()
            await crud.create_pending_generation(
                db,
                request_id="newer-missing-cache",
                image_hash=row.image_hash,
                preset_id=row.preset_id,
                instruction_hash=row.instruction_hash,
                prompt_version=row.prompt_version,
                model=row.model,
                original_path=row.original_path,
                prompt=row.prompt,
            )
            await crud.mark_generation_success(
                db,
                request_id="newer-missing-cache",
                output_path=str(real_settings.output_dir / "missing-cache.png"),
                image_url=None,
            )

    asyncio.run(_add_newer_missing_cache())

    async def _raise_if_called(**kwargs: object) -> str:
        raise AssertionError("OpenAI should not be called when older cache is readable")

    monkeypatch.setattr(generation_service, "call_openai_edit", _raise_if_called)

    second = asyncio.run(
        image_edit.edit_image(
            image_data_url=TINY_PNG_DATA_URL,
            preset=preset,
            user_prompt="same prompt",
            settings=real_settings,
        )
    )

    assert second["note"] == "캐시된 결과 재사용"
    assert second["image_url"] == first["image_url"]


def test_generate_reuses_original_file_for_same_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    first = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "밝게 해주세요",
        },
    )
    second = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "어둡게 해주세요",
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200

    async def _original_paths() -> list[str | None]:
        async with async_session_scope() as db:
            result = await db.execute(select(Generation.original_path).order_by(Generation.id))
            return list(result.scalars().all())

    original_paths = asyncio.run(_original_paths())
    assert len(original_paths) == 2
    assert original_paths[0] == original_paths[1]
    assert original_paths[0] is not None
    assert Path(original_paths[0]).exists()


def test_generate_does_not_use_logo_reference_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_call: dict[str, object] = {}

    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        captured_call.update(kwargs)
        return TINY_PNG_B64, {}

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
        },
    )

    assert response.status_code == 200

    async def _db_state() -> tuple[str | None, str]:
        async with async_session_scope() as db:
            result = await db.execute(select(Generation))
            generation = result.scalar_one()
            return (
                generation.user_copy,
                generation.instruction_hash,
            )

    (
        user_copy,
        instruction_hash,
    ) = asyncio.run(_db_state())
    assert user_copy is None
    assert instruction_hash != crud.instruction_sha256("bright mood")
    assert "reference_images" not in captured_call


def test_generate_stores_rendered_user_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

    async def _fake_copy(**kwargs: object) -> CopyGenerationResult:
        return CopyGenerationResult(
            copy=AdCopy(
                headline="오늘 놓치기 아까운 딸기 케이크 6,500원",
                subcopy="카페에서 즐기는 신선한 메뉴를 더 맛있게 전해드려요.",
                cta="지금 방문해보세요",
                mode="rewrite",
            )
        )

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    monkeypatch.setattr(openai_copy, "call_openai_copy", _fake_copy)
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
            "adCopyEnabled": True,
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
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

    async def _fake_copy(**kwargs: object) -> CopyGenerationResult:
        return CopyGenerationResult(
            copy=AdCopy(
                headline="라떼 4,500원",
                subcopy="카페에서 더 맛있게 즐겨보세요.",
                cta=None,
                mode="polish",
            )
        )

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    monkeypatch.setattr(openai_copy, "call_openai_copy", _fake_copy)
    force_openai_mode(monkeypatch)

    payload = {
        "imageDataUrl": TINY_PNG_DATA_URL,
        "presetId": "instagram",
        "detailType": "square_feed",
        "userPrompt": "bright mood",
        "userCopy": "라떼 4500원",
        "copyMode": "polish",
        "adCopyEnabled": True,
    }
    first = client.post("/api/generate", json=payload)
    second = client.post("/api/generate", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["note"] == "캐시된 결과 재사용"
    assert second.json()["imageUrl"].startswith("/outputs/")
    assert second.json()["imageDataUrl"] is None

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
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

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


def test_generate_ignores_user_copy_when_ad_copy_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_call(**kwargs: object) -> tuple[str, dict[str, object]]:
        return TINY_PNG_B64, {}

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
            "adCopyEnabled": False,
        },
    )

    assert response.status_code == 200

    async def _saved_user_copy() -> str | None:
        async with async_session_scope() as db:
            result = await db.execute(select(Generation.user_copy))
            return result.scalar_one()

    assert asyncio.run(_saved_user_copy()) is None
