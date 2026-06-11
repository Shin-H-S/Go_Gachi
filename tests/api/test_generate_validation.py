import asyncio
import base64
from io import BytesIO

import pytest
from PIL import Image
from sqlalchemy import func, select

from backend.app.db.database import async_session_scope
from backend.app.db.models import ApiUsage, Generation
from backend.app.services import image_edit
from tests.api.helpers import (
    TINY_PNG_B64,
    TINY_PNG_DATA_URL,
    client,
    image_size_from_data_url,
)


def test_generate_mock_mode_succeeds_without_db_record() -> None:
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": None,
            "userPrompt": "",
            "targetWidth": 1200,
            "targetHeight": 900,
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["provider"] == "mock"
    assert body["imageUrl"] is None
    assert image_size_from_data_url(body["imageDataUrl"]) == (1200, 900)

    async def _counts() -> tuple[int, int]:
        async with async_session_scope() as db:
            gen_result = await db.execute(select(func.count()).select_from(Generation))
            usage_result = await db.execute(select(func.count()).select_from(ApiUsage))
            return int(gen_result.scalar_one()), int(usage_result.scalar_one())

    assert asyncio.run(_counts()) == (0, 0)


def test_generate_rejects_invalid_image_data_url() -> None:
    response = client.post(
        "/api/generate",
        json={"imageDataUrl": "not-a-data-url", "presetId": None, "userPrompt": ""},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "INVALID_IMAGE_INPUT"
    assert "이미지" in detail["message"]


def test_generate_rejects_unknown_preset_id() -> None:
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "unknown_preset",
            "userPrompt": "",
        },
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "UNSUPPORTED_PRESET_ID"
    assert "presetId" in detail["message"]


def test_generate_rejects_unknown_detail_type() -> None:
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "detailType": "unknown_detail",
            "userPrompt": "",
        },
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "UNSUPPORTED_DETAIL_TYPE"
    assert "detailType" in detail["message"]


def test_generate_rejects_incomplete_target_size() -> None:
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": None,
            "userPrompt": "",
            "targetWidth": 1200,
        },
    )

    assert response.status_code == 422


def test_generate_rejects_unknown_resize_mode() -> None:
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "resizeMode": "stretch",
        },
    )

    assert response.status_code == 422


def test_generate_rejects_legacy_feedback_field() -> None:
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "feedback": "legacy field",
        },
    )

    assert response.status_code == 422


def test_generate_rejects_unknown_copy_mode() -> None:
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "copyMode": "aggressive",
        },
    )

    assert response.status_code == 422


def test_generate_rejects_unknown_logo_position() -> None:
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "logoPosition": "middle_somewhere",
        },
    )

    assert response.status_code == 422


def test_generate_rejects_too_long_user_copy() -> None:
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "userCopy": "a" * 301,
        },
    )

    assert response.status_code == 422


def test_auto_copy_generate_endpoint_is_backend_owned_contract() -> None:
    response = client.post(
        "/api/copy/generate",
        json={
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "광고 유형: 정사각형 피드",
            "copyMode": "rewrite",
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["headline"]
    assert body["copyMode"] == "rewrite"


def test_generate_rejects_too_long_logo_data_url() -> None:
    response = client.post(
        "/api/generate",
        json={
            "imageDataUrl": TINY_PNG_DATA_URL,
            "presetId": "instagram",
            "logoDataUrl": "a" * 8_000_001,
        },
    )

    assert response.status_code == 422


def test_render_target_png_contain_preserves_full_image() -> None:
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


def test_generate_normalizes_uploaded_image_before_openai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = Image.new("CMYK", (3, 2), (0, 128, 128, 0))
    source_buffer = BytesIO()
    source.save(source_buffer, format="JPEG")
    data_url = (
        f"data:image/jpeg;base64,{base64.b64encode(source_buffer.getvalue()).decode('ascii')}"
    )
    captured: dict[str, image_edit.UploadedImage] = {}

    async def _fake_call(**kwargs: object) -> str:
        captured["uploaded"] = kwargs["uploaded"]
        return TINY_PNG_B64

    from backend.app.services import generation_service
    from tests.api.helpers import force_openai_mode

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": data_url, "presetId": None, "userPrompt": ""},
    )

    assert response.status_code == 200
    uploaded = captured["uploaded"]
    assert uploaded.mime_type == "image/png"
    assert uploaded.extension == "png"
    assert uploaded.info.format == "PNG"
    assert uploaded.info.mode == "RGB"
    assert uploaded.info.width == 3
    assert uploaded.info.height == 2
