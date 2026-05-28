"""/api/* 엔드포인트 e2e 테스트.

테스트 모드는 mock provider 기본. 캐시 경로(openai 분기)는 마지막 케이스에서
monkeypatch로 _call_openai_edit를 가짜 응답으로 바꿔 확인한다.
"""

import asyncio
import base64
import re
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from backend.app.api import internal
from backend.app.core.config import Settings, get_settings
from backend.app.core.presets import default_preset
from backend.app.db.database import async_init_db, async_session_scope
from backend.app.db.models import ApiUsage, Generation
from backend.app.main import IMAGE_GENERATION_UNAVAILABLE_MESSAGE, app
from backend.app.services import image_edit
from backend.app.services.costs import CostSnapshot

# 1x1 투명 PNG (base64). multipart 업로드 없이 data URL 형식만 검증할 때 쓴다.
TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhg"
    "GAWjR9awAAAABJRU5ErkJggg=="
)
TINY_PNG_DATA_URL = f"data:image/png;base64,{TINY_PNG_B64}"

client = TestClient(app)


def force_openai_mode(
    monkeypatch: pytest.MonkeyPatch,
    *,
    api_key: str = "test-key",
) -> Settings:
    """테스트 동안 settings를 OpenAI provider 모드로 강제한다."""
    real_settings = get_settings()
    monkeypatch.setattr(real_settings, "image_provider", "openai")
    monkeypatch.setattr(real_settings, "openai_api_key", api_key)
    return real_settings


@pytest.fixture(autouse=True)
def clean_db() -> Iterator[None]:
    """각 테스트 시작 전에 generations/api_usage 테이블을 비운다."""

    async def _clean() -> None:
        await async_init_db()
        async with async_session_scope() as db:
            await db.execute(Generation.__table__.delete())
            await db.execute(ApiUsage.__table__.delete())

    asyncio.run(_clean())
    yield


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_internal_usage_returns_budget_keys() -> None:
    """admin key가 없을 때는 추정 비용 + 예산 정보만 깔끔하게 돌려준다."""
    response = client.get("/api/internal/usage")
    body = response.json()

    assert response.status_code == 200
    for key in (
        "total_estimated_cost",
        "generation_count",
        "cached_count",
        "budget_limit",
        "budget_alert",
        "remaining",
    ):
        assert key in body
    # admin key 없으니 actual_* 필드는 응답에 끼지 않는다.
    assert "actual_total_cost" not in body
    assert "actual_currency" not in body
    assert "cost_sync_error" not in body
    # 빈 DB 상태이므로 모두 0
    assert body["total_estimated_cost"] == 0.0
    assert body["generation_count"] == 0
    assert body["cached_count"] == 0
    # 잔여 = 한도(기본 30.0)
    assert body["remaining"] == body["budget_limit"]


def test_internal_usage_includes_actual_cost_when_admin_key_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Admin key가 있으면 actual_* 필드도 함께 노출되고 remaining은 그대로 우리 추정 기준."""
    real_settings = get_settings()
    monkeypatch.setattr(real_settings, "openai_admin_key", "admin-key")

    async def _fake_cost(settings):  # noqa: ANN001, ANN202
        return CostSnapshot(
            total_cost=1.59,
            currency="usd",
            start_time=1764547200,
            end_time=1764806400,
        )

    monkeypatch.setattr(internal.costs, "fetch_current_month_cost", _fake_cost)

    response = client.get("/api/internal/usage")
    body = response.json()

    assert response.status_code == 200
    assert body["total_estimated_cost"] == 0.0
    assert body["actual_total_cost"] == 1.59
    assert body["actual_currency"] == "usd"
    # remaining은 우리 앱 내부 추정 기준만 사용한다(조직 전체 비용 섞지 않음).
    assert body["remaining"] == body["budget_limit"]


def test_generate_mock_mode_succeeds_without_db_record() -> None:
    """mock 모드는 DB·캐시 모두 건너뛰고 원본 이미지를 그대로 돌려준다."""
    assert get_settings().image_provider == "mock"

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "feedback": ""},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["provider"] == "mock"
    assert body["imageDataUrl"] == TINY_PNG_DATA_URL

    # mock은 DB에 흔적을 남기지 않는다.
    async def _counts() -> tuple[int, int]:
        async with async_session_scope() as db:
            gen_result = await db.execute(select(func.count()).select_from(Generation))
            usage_result = await db.execute(select(func.count()).select_from(ApiUsage))
            return int(gen_result.scalar_one()), int(usage_result.scalar_one())

    gen_count, usage_count = asyncio.run(_counts())
    assert gen_count == 0
    assert usage_count == 0


def test_generate_rejects_invalid_image_data_url() -> None:
    """잘못된 data URL은 400으로 사용자에게 돌려준다."""
    response = client.post(
        "/api/generate",
        json={"imageDataUrl": "not-a-data-url", "presetId": None, "feedback": ""},
    )

    assert response.status_code == 400
    assert "이미지" in response.json()["detail"]


def test_generate_rejects_unknown_preset_id() -> None:
    """잘못된 presetId는 기본값으로 숨기지 않고 400으로 알려준다."""
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "unknown_preset",
            "feedback": "",
        },
    )

    assert response.status_code == 400
    assert "presetId" in response.json()["detail"]


def test_generate_returns_503_when_openai_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenAI 모드인데 API 키가 없으면 사용자 입력 문제가 아니라 서비스 불가로 본다."""
    force_openai_mode(monkeypatch, api_key="")

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "feedback": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_generate_returns_503_when_provider_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenAI 호출 실패도 400이 아니라 서비스 의존성 실패로 분류한다."""

    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        raise RuntimeError("provider exploded")

    monkeypatch.setattr(image_edit, "_call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "feedback": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_generate_returns_503_when_network_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenAI 연결 자체가 실패해도(httpx.HTTPError) 500이 아니라 503으로 떨어진다."""

    class _BoomClient:
        def __init__(self, *args, **kwargs):  # noqa: ARG002, ANN003
            pass

        async def __aenter__(self):  # noqa: ANN202
            return self

        async def __aexit__(self, *args):  # noqa: ANN003, ANN202
            return None

        async def post(self, *args, **kwargs):  # noqa: ANN003, ARG002, ANN202
            raise httpx.ConnectError("network down")

    monkeypatch.setattr(image_edit.httpx, "AsyncClient", _BoomClient)

    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "feedback": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_openai_cache_hit_on_repeated_input(monkeypatch: pytest.MonkeyPatch) -> None:
    """같은 입력으로 두 번 호출하면 두 번째는 캐시 hit(`cached=True`)이 되어야 한다."""
    # OpenAI 실호출은 막고, 결정적인 PNG b64를 반환하도록 _call_openai_edit를 가짜로 교체.
    fake_b64 = TINY_PNG_B64

    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return fake_b64

    monkeypatch.setattr(image_edit, "_call_openai_edit", _fake_call)
    real_settings = force_openai_mode(monkeypatch)

    preset = default_preset()

    # 첫 호출: 실제 OpenAI 분기 → mark_success + usage(cost>0, cached=False)
    result1 = asyncio.run(
        image_edit.edit_image(
            image_data_url=TINY_PNG_DATA_URL,
            preset=preset,
            feedback="밝게 해주세요",
            settings=real_settings,
        )
    )
    assert result1["provider"] == "openai"
    assert result1["image_data_url"].startswith("data:image/png;base64,")

    # 두 번째 호출: 같은 image + preset + feedback → 캐시 hit
    result2 = asyncio.run(
        image_edit.edit_image(
            image_data_url=TINY_PNG_DATA_URL,
            preset=preset,
            feedback="밝게 해주세요",
            settings=real_settings,
        )
    )
    assert result2["provider"] == "openai"
    assert result2["note"] == "캐시된 결과 재사용"

    # DB 상태 검증: success 1건 + cached 1건, usage 2건 (cached=True 1건)
    async def _db_state() -> tuple[list[str], int, int]:
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
    assert generation_rows[0].original_path is not None
    assert generation_rows[0].output_path is not None
    assert generation_rows[1].original_path == generation_rows[0].original_path
    assert Path(generation_rows[0].original_path).exists()
    assert Path(generation_rows[0].output_path).exists()
    assert re.fullmatch(
        r"\d{8}_\d{6}_[0-9a-f]{6}\.png",
        Path(generation_rows[0].output_path).name,
    )
    assert re.fullmatch(
        r"\d{8}_\d{6}_[0-9a-f]{6}\.png",
        Path(generation_rows[0].original_path).with_suffix(".png").name,
    )
    assert Path(generation_rows[0].original_path).read_bytes() == base64.b64decode(TINY_PNG_B64)
    assert cached_usage_count == 1
    assert total_usage_count == 2
