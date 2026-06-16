import asyncio
import base64

from backend.app.core.auth import AuthUser, get_current_user
from backend.app.core.config import get_settings
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.main import app
from tests.api.helpers import TINY_PNG_B64, client
from tests.api.mypage_helpers import user as make_user


def test_my_uploads_returns_unique_original_images_without_inline_data() -> None:
    user = make_user("user-upload-check")
    settings = get_settings()
    original_file = settings.upload_dir / "original-menu.png"
    original_file.write_bytes(base64.b64decode(TINY_PNG_B64))
    missing_file = settings.upload_dir / "missing-menu.png"

    async def _override_user() -> AuthUser:
        return user

    async def _seed() -> None:
        async with async_session_scope() as db:
            for request_id, preset_id, image_hash, original_path in (
                ("upload-first", "instagram", "same-menu-hash", original_file),
                ("upload-second", "daangn", "same-menu-hash", original_file),
                ("upload-missing", "instagram", "missing-menu-hash", missing_file),
            ):
                await crud.create_pending_generation(
                    db,
                    request_id=request_id,
                    image_hash=image_hash,
                    preset_id=preset_id,
                    instruction_hash=f"instruction-{request_id}",
                    prompt_version="prompt-v-test",
                    model="model-test",
                    original_path=str(original_path),
                    prompt=None,
                    user_id=user.id,
                )
                if request_id != "upload-missing":
                    await crud.mark_generation_success(
                        db,
                        request_id=request_id,
                        output_path=str(settings.output_dir / f"{request_id}.png"),
                        image_url=None,
                    )

    asyncio.run(_seed())
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.get("/api/auth/me/uploads")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["upload_id"] == "same-menu-hash"
    assert body["items"][0]["used_count"] == 2
    assert body["items"][0]["original_image_url"] == "/uploads/original-menu.png"
    assert "image_data_url" not in body["items"][0]


def test_my_uploads_keeps_r2_url_when_local_file_is_not_available(monkeypatch) -> None:
    user = make_user("user-upload-r2-check")

    async def _override_user() -> AuthUser:
        return user

    async def _fake_upload_url(path: str | None) -> str | None:
        return f"https://pub.example/{path}" if path else None

    async def _seed() -> None:
        async with async_session_scope() as db:
            await crud.create_pending_generation(
                db,
                request_id="r2-upload",
                image_hash="r2-menu-hash",
                preset_id="instagram",
                instruction_hash="instruction-r2-upload",
                prompt_version="prompt-v-test",
                model="model-test",
                original_path="uploads/r2-menu.png",
                prompt=None,
                user_id=user.id,
            )

    asyncio.run(_seed())
    monkeypatch.setattr(
        "backend.app.api.mypage_upload_data.upload_url_if_exists_async",
        _fake_upload_url,
    )
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.get("/api/auth/me/uploads")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["original_image_url"] == "https://pub.example/uploads/r2-menu.png"
    assert "image_data_url" not in body["items"][0]
