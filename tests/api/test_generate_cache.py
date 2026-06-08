import asyncio
import base64
import re
from pathlib import Path

import pytest
from sqlalchemy import func, select

from backend.app.core.presets import default_preset
from backend.app.db.database import async_session_scope
from backend.app.db.models import ApiUsage, Generation
from backend.app.services import generation_service, image_edit
from tests.api.helpers import TINY_PNG_B64, TINY_PNG_DATA_URL, force_openai_mode


def test_openai_cache_hit_on_repeated_input(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    real_settings = force_openai_mode(monkeypatch)
    preset = default_preset()

    result1 = asyncio.run(
        image_edit.edit_image(
            image_data_url=TINY_PNG_DATA_URL,
            preset=preset,
            feedback="밝게 해주세요",
            settings=real_settings,
        )
    )
    result2 = asyncio.run(
        image_edit.edit_image(
            image_data_url=TINY_PNG_DATA_URL,
            preset=preset,
            feedback="밝게 해주세요",
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
