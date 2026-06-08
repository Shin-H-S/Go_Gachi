import asyncio
import base64

from backend.app.core.auth import AuthUser, get_current_user
from backend.app.core.config import get_settings
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.main import app
from tests.api.helpers import TINY_PNG_B64, client


def _user(user_id: str = "user-check") -> AuthUser:
    return AuthUser(
        id=user_id,
        email=f"{user_id}@example.com",
        role="user",
        display_name="User",
    )


def test_my_generations_hides_image_url_when_output_file_is_missing() -> None:
    user = _user("user-image-url-check")
    settings = get_settings()
    existing_output = settings.output_dir / "existing-result.png"
    missing_output = settings.output_dir / "missing-result.png"
    existing_output.write_bytes(b"png")

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
                original_path=None,
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
                original_path=None,
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
    assert items["missing-file"]["image_url"] is None


def test_my_folders_can_be_created_and_assigned_to_generation() -> None:
    user = _user("user-folder-check")
    settings = get_settings()
    output_file = settings.output_dir / "folder-result.png"
    output_file.write_bytes(base64.b64decode(TINY_PNG_B64))

    async def _override_user() -> AuthUser:
        return user

    async def _seed() -> None:
        async with async_session_scope() as db:
            await crud.create_pending_generation(
                db,
                request_id="folder-target",
                image_hash="folder-image-hash",
                preset_id="instagram",
                instruction_hash="folder-instruction",
                prompt_version="prompt-v-test",
                model="model-test",
                original_path=None,
                prompt=None,
                user_id=user.id,
            )
            await crud.mark_generation_success(
                db, request_id="folder-target", output_path=str(output_file), image_url=None
            )

    asyncio.run(_seed())
    app.dependency_overrides[get_current_user] = _override_user
    try:
        create_response = client.post("/api/auth/me/folders", json={"name": "봄 신메뉴"})
        folder_id = create_response.json()["id"]
        list_response = client.get("/api/auth/me/folders")
        move_response = client.patch(
            "/api/auth/me/generations/folder-target/folder",
            json={"folder_id": folder_id},
        )
        generations_response = client.get("/api/auth/me/generations")
        unassign_response = client.patch(
            "/api/auth/me/generations/folder-target/folder",
            json={"folder_id": None},
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert create_response.status_code == 201
    assert create_response.json()["name"] == "봄 신메뉴"
    assert list_response.json()["items"] == [create_response.json()]
    assert move_response.json() == {"request_id": "folder-target", "folder_id": folder_id}
    assert generations_response.json()["items"][0]["folder_id"] == folder_id
    assert unassign_response.json() == {"request_id": "folder-target", "folder_id": None}


def test_my_uploads_returns_unique_original_images_as_data_urls() -> None:
    user = _user("user-upload-check")
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
    assert body["items"][0]["image_data_url"].startswith("data:image/png;base64,")
