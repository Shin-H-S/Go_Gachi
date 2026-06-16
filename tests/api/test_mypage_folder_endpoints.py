import asyncio
import base64

from backend.app.core.auth import AuthUser, get_current_user
from backend.app.core.config import get_settings
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.main import app
from tests.api.helpers import TINY_PNG_B64, client
from tests.api.mypage_helpers import user as make_user


def test_my_folders_can_be_created_and_assigned_to_generation() -> None:
    user = make_user("user-folder-check")
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


def test_my_folders_can_be_renamed_and_deleted_to_uncategorize_generations() -> None:
    user = make_user("user-folder-manage")

    async def _override_user() -> AuthUser:
        return user

    async def _seed() -> None:
        async with async_session_scope() as db:
            await crud.create_pending_generation(
                db,
                request_id="folder-managed-target",
                image_hash="folder-managed-image-hash",
                preset_id="instagram",
                instruction_hash="folder-managed-instruction",
                prompt_version="prompt-v-test",
                model="model-test",
                original_path=None,
                prompt=None,
                user_id=user.id,
            )

    asyncio.run(_seed())
    app.dependency_overrides[get_current_user] = _override_user
    try:
        create_response = client.post("/api/auth/me/folders", json={"name": "봄 신메뉴"})
        folder_id = create_response.json()["id"]
        assign_response = client.patch(
            "/api/auth/me/generations/folder-managed-target/folder",
            json={"folder_id": folder_id},
        )
        rename_response = client.patch(
            f"/api/auth/me/folders/{folder_id}",
            json={"name": "여름 신메뉴"},
        )
        delete_response = client.delete(f"/api/auth/me/folders/{folder_id}")
        list_response = client.get("/api/auth/me/folders")
        generations_response = client.get("/api/auth/me/generations")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert create_response.status_code == 201
    assert assign_response.status_code == 200
    assert rename_response.status_code == 200
    assert rename_response.json()["name"] == "여름 신메뉴"
    assert delete_response.status_code == 204
    assert list_response.json() == {"items": [], "count": 0}
    assert generations_response.json()["items"][0]["folder_id"] is None
