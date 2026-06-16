import asyncio

from backend.app.core.auth import AuthUser, get_current_user
from backend.app.core.config import get_settings
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.main import app
from tests.api.helpers import client
from tests.api.mypage_helpers import user as make_user


def test_my_generations_hides_image_url_when_output_file_is_missing() -> None:
    user = make_user("user-image-url-check")
    settings = get_settings()
    existing_output = settings.output_dir / "existing-result.png"
    missing_output = settings.output_dir / "missing-result.png"
    existing_upload = settings.upload_dir / "existing-original.png"
    missing_upload = settings.upload_dir / "missing-original.png"
    existing_output.write_bytes(b"png")
    existing_upload.write_bytes(b"png")

    async def _override_user() -> AuthUser:
        return user

    async def _seed() -> None:
        async with async_session_scope() as db:
            await crud.create_pending_generation(
                db,
                request_id="existing-file",
                image_hash="hash-existing",
                preset_id="instagram",
                instruction_hash="instruction-existing",
                prompt_version="prompt-v-test",
                model="model-test",
                original_path=str(existing_upload),
                prompt=None,
                user_id=user.id,
            )
            await crud.mark_generation_success(
                db, request_id="existing-file", output_path=str(existing_output), image_url=None
            )
            await crud.create_pending_generation(
                db,
                request_id="missing-file",
                image_hash="hash-missing",
                preset_id="instagram",
                instruction_hash="instruction-missing",
                prompt_version="prompt-v-test",
                model="model-test",
                original_path=str(missing_upload),
                prompt=None,
                user_id=user.id,
            )
            await crud.mark_generation_success(
                db, request_id="missing-file", output_path=str(missing_output), image_url=None
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
    assert (
        items["existing-file"]["download_url"] == "/api/assets/download/outputs/existing-result.png"
    )
    assert items["existing-file"]["original_image_url"] == "/uploads/existing-original.png"
    assert items["missing-file"]["image_url"] is None
    assert items["missing-file"]["download_url"] is None
    assert items["missing-file"]["original_image_url"] is None


def test_my_generations_supports_page_and_total_count() -> None:
    user = make_user("user-page-check")

    async def _override_user() -> AuthUser:
        return user

    async def _seed() -> None:
        async with async_session_scope() as db:
            for idx in range(14):
                await crud.create_pending_generation(
                    db,
                    request_id=f"api-page-{idx:02d}",
                    image_hash=f"api-page-hash-{idx:02d}",
                    preset_id="instagram",
                    instruction_hash=f"api-page-instruction-{idx:02d}",
                    prompt_version="prompt-v-test",
                    model="model-test",
                    original_path=None,
                    prompt=None,
                    user_id=user.id,
                )
            await crud.create_pending_generation(
                db,
                request_id="api-page-other",
                image_hash="api-page-hash-other",
                preset_id="instagram",
                instruction_hash="api-page-instruction-other",
                prompt_version="prompt-v-test",
                model="model-test",
                original_path=None,
                prompt=None,
                user_id="other-user",
            )

    asyncio.run(_seed())
    app.dependency_overrides[get_current_user] = _override_user
    try:
        first = client.get("/api/auth/me/generations")
        second = client.get("/api/auth/me/generations?page=2")
        empty = client.get("/api/auth/me/generations?page=3")
        invalid = client.get("/api/auth/me/generations?page=0")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert first.status_code == 200
    assert first.json()["count"] == 12
    assert first.json()["total_count"] == 14
    assert [item["request_id"] for item in first.json()["items"]] == [
        f"api-page-{idx:02d}" for idx in range(13, 1, -1)
    ]
    assert second.status_code == 200
    assert second.json()["count"] == 2
    assert second.json()["total_count"] == 14
    assert [item["request_id"] for item in second.json()["items"]] == [
        "api-page-01",
        "api-page-00",
    ]
    assert empty.status_code == 200
    assert empty.json() == {"items": [], "count": 0, "total_count": 14}
    assert invalid.status_code == 422
