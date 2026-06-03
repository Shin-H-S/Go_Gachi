"""/api/* 엔드포인트 e2e 테스트.

테스트 모드는 mock provider 기본. 캐시 경로(openai 분기)는 일부 케이스에서
generation_service.call_openai_edit를 가짜 응답으로 바꿔 확인한다.
"""

import asyncio
import base64
import re
from collections.abc import Iterator
from io import BytesIO
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import func, select

from backend.app.api import internal
from backend.app.core.auth import AuthUser, get_current_user
from backend.app.core.config import Settings, get_settings
from backend.app.core.presets import default_preset
from backend.app.db import crud
from backend.app.db.database import async_init_db, async_session_scope
from backend.app.db.models import ApiUsage, Generation
from backend.app.main import IMAGE_GENERATION_UNAVAILABLE_MESSAGE, app
from backend.app.services import generation_service, image_edit, openai_images
from backend.app.services.costs import CostSnapshot

# 1x1 투명 PNG (base64). multipart 업로드 없이 data URL 형식만 검증할 때 쓴다.
TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhg"
    "GAWjR9awAAAABJRU5ErkJggg=="
)
TINY_PNG_DATA_URL = f"data:image/png;base64,{TINY_PNG_B64}"

client = TestClient(app)


def image_size_from_data_url(data_url: str) -> tuple[int, int]:
    """응답 data URL의 실제 PNG 픽셀 크기를 확인한다."""
    _, encoded = data_url.split(",", 1)
    with Image.open(BytesIO(base64.b64decode(encoded))) as image:
        return image.size


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
    """mock 모드는 DB·캐시를 건너뛰되 선택한 상세 크기로 이미지를 돌려준다."""
    assert get_settings().image_provider == "mock"

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": None,
            "feedback": "",
            "targetWidth": 1200,
            "targetHeight": 900,
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["provider"] == "mock"
    assert body["imageUrl"] is None
    assert image_size_from_data_url(body["imageDataUrl"]) == (1200, 900)

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


def test_generate_rejects_unknown_detail_type() -> None:
    """프리셋에 없는 detailType은 400으로 알려준다."""
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram_square",
            "detailType": "unknown_detail",
            "feedback": "",
        },
    )

    assert response.status_code == 400
    assert "detailType" in response.json()["detail"]


def test_generate_rejects_incomplete_target_size() -> None:
    """상세 출력 크기는 width/height를 함께 보내야 한다."""
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": None,
            "feedback": "",
            "targetWidth": 1200,
        },
    )

    assert response.status_code == 422


def test_generate_rejects_unknown_resize_mode() -> None:
    """지원하지 않는 resizeMode는 요청 스키마 단계에서 거절한다."""
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram_square",
            "resizeMode": "stretch",
        },
    )

    assert response.status_code == 422


def test_render_target_png_contain_preserves_full_image() -> None:
    """contain 모드는 원본 전체를 중앙에 보존하고 최종 크기는 정확히 맞춘다."""
    source = Image.new("RGB", (4, 8), "#ffffff")
    for y in range(8):
        source.putpixel((0, y), (255, 0, 0))
        source.putpixel((3, y), (0, 128, 0))

    source_buffer = BytesIO()
    source.save(source_buffer, format="PNG")

    rendered = image_edit.render_target_png(
        source_buffer.getvalue(),
        image_edit.TargetSize(width=8, height=8),
        "contain",
    )

    with Image.open(BytesIO(rendered)) as image:
        assert image.size == (8, 8)
        assert image.getpixel((2, 0)) == (255, 0, 0)
        assert image.getpixel((5, 0)) == (0, 128, 0)


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

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
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

    monkeypatch.setattr(openai_images.httpx, "AsyncClient", _BoomClient)

    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "feedback": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_generate_returns_503_when_openai_result_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenAI 성공 응답이라도 data가 비어 있으면 500이 아니라 503으로 정리한다."""

    class _EmptyDataResponse:
        status_code = 200

        def json(self) -> dict[str, list[dict[str, str]]]:
            return {"data": []}

    class _EmptyDataClient:
        def __init__(self, *args, **kwargs):  # noqa: ARG002, ANN003
            pass

        async def __aenter__(self):  # noqa: ANN202
            return self

        async def __aexit__(self, *args):  # noqa: ANN003, ANN202
            return None

        async def post(self, *args, **kwargs):  # noqa: ANN003, ARG002, ANN202
            return _EmptyDataResponse()

    monkeypatch.setattr(openai_images.httpx, "AsyncClient", _EmptyDataClient)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "feedback": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_generate_returns_503_when_openai_result_base64_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenAI 결과 base64가 깨져 있으면 500이 아니라 503으로 정리한다."""

    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return "not-valid-base64!"

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "feedback": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_generate_returns_503_when_openai_result_is_not_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenAI 결과가 base64여도 이미지가 아니면 500이 아니라 503으로 정리한다."""
    fake_b64 = base64.b64encode(b"not-an-image").decode("ascii")

    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return fake_b64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "feedback": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_generate_normalizes_uploaded_image_before_openai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CMYK JPEG처럼 모드가 특이한 이미지도 OpenAI 호출 전 PNG/RGB로 정리한다."""
    source = Image.new("CMYK", (3, 2), (0, 128, 128, 0))
    source_buffer = BytesIO()
    source.save(source_buffer, format="JPEG")
    data_url = (
        f"data:image/jpeg;base64,{base64.b64encode(source_buffer.getvalue()).decode('ascii')}"
    )
    captured: dict[str, image_edit.UploadedImage] = {}

    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        captured["uploaded"] = kwargs["uploaded"]
        return TINY_PNG_B64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": data_url, "presetId": None, "feedback": ""},
    )

    assert response.status_code == 200
    uploaded = captured["uploaded"]
    assert uploaded.mime_type == "image/png"
    assert uploaded.extension == "png"
    assert uploaded.info.format == "PNG"
    assert uploaded.info.mode == "RGB"
    assert uploaded.info.width == 3
    assert uploaded.info.height == 2
    with Image.open(BytesIO(uploaded.content)) as normalized:
        assert normalized.format == "PNG"
        assert normalized.mode == "RGB"
        assert normalized.size == (3, 2)


def test_generate_hides_prompt_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """production 응답에서는 내부 프롬프트를 노출하지 않는다."""
    fake_b64 = TINY_PNG_B64

    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return fake_b64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    real_settings = force_openai_mode(monkeypatch)
    monkeypatch.setattr(real_settings, "app_env", "production")

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "feedback": ""},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["provider"] == "openai"
    assert body["prompt"] is None


def test_generate_openai_result_matches_target_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenAI 결과도 최종 응답 전에 선택 상세 크기로 후처리한다."""
    fake_b64 = TINY_PNG_B64

    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return fake_b64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram_square",
            "detailType": "story_image",
            "feedback": "밝게",
            "targetWidth": 1080,
            "targetHeight": 1920,
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["provider"] == "openai"
    assert body["imageUrl"].startswith("/outputs/")
    assert body["imageUrl"].endswith(".png")
    assert "://" not in body["imageUrl"]
    assert image_size_from_data_url(body["imageDataUrl"]) == (1080, 1920)
    assert "1080x1920" in body["prompt"]
    assert "story_image" in body["prompt"]
    assert "Instagram Story" in body["prompt"]


def test_generate_exposes_prompt_in_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """local 환경에서는 디버깅을 위해 프롬프트가 응답에 그대로 들어있어야 한다."""
    fake_b64 = TINY_PNG_B64

    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return fake_b64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    real_settings = force_openai_mode(monkeypatch)
    # 기본 app_env는 "local". production 조건을 잘못 뒤집어도 이 테스트가 잡는다.
    assert real_settings.app_env != "production"

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "feedback": ""},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["provider"] == "openai"
    assert body["prompt"] is not None
    assert "cafe" in body["prompt"].lower()


def test_my_generations_hides_image_url_when_output_file_is_missing() -> None:
    """마이페이지는 DB 기록이 있어도 실제 결과 파일이 없으면 image_url을 null로 내려준다."""
    user = AuthUser(
        id="user-image-url-check",
        email="user@example.com",
        role="user",
        display_name="User",
    )

    async def _override_user() -> AuthUser:
        return user

    settings = get_settings()
    existing_output = settings.output_dir / "existing-result.png"
    missing_output = settings.output_dir / "missing-result.png"
    existing_output.write_bytes(b"png")

    async def _seed() -> None:
        async with async_session_scope() as db:
            await crud.create_pending_generation(
                db,
                request_id="existing-file",
                image_hash="hash-existing",
                preset_id="instagram_square",
                instruction_hash="instruction-existing",
                prompt_version="prompt-v-test",
                model="model-test",
                original_path=None,
                prompt=None,
                user_id=user.id,
            )
            await crud.mark_generation_success(
                db,
                request_id="existing-file",
                output_path=str(existing_output),
                image_url=None,
            )
            await crud.create_pending_generation(
                db,
                request_id="missing-file",
                image_hash="hash-missing",
                preset_id="instagram_square",
                instruction_hash="instruction-missing",
                prompt_version="prompt-v-test",
                model="model-test",
                original_path=None,
                prompt=None,
                user_id=user.id,
            )
            await crud.mark_generation_success(
                db,
                request_id="missing-file",
                output_path=str(missing_output),
                image_url=None,
            )

    asyncio.run(_seed())
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.get("/api/auth/me/generations")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    items = {item["request_id"]: item for item in response.json()["items"]}
    assert items["existing-file"]["image_url"] == "/outputs/existing-result.png"
    assert items["missing-file"]["image_url"] is None


def test_openai_cache_hit_on_repeated_input(monkeypatch: pytest.MonkeyPatch) -> None:
    """같은 입력으로 두 번 호출하면 두 번째는 캐시 hit(`cached=True`)이 되어야 한다."""
    # OpenAI 실호출은 막고, 결정적인 PNG b64를 반환하도록 call_openai_edit를 가짜로 교체.
    fake_b64 = TINY_PNG_B64

    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return fake_b64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
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
    assert result1["image_url"].startswith("/outputs/")
    assert "://" not in result1["image_url"]

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
    assert result2["image_url"] == result1["image_url"]
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
