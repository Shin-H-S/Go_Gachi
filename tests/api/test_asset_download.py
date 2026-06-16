import asyncio
from pathlib import Path

from backend.app.core.auth import AuthUser, get_current_user
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.main import app
from tests.api.helpers import client


def _user(user_id: str) -> AuthUser:
    return AuthUser(
        id=user_id,
        email=f"{user_id}@example.com",
        role="user",
        display_name="User",
    )


async def _seed_success_generation(
    *,
    request_id: str,
    user_id: str,
    output_path: str,
) -> None:
    async with async_session_scope() as db:
        await crud.create_pending_generation(
            db,
            request_id=request_id,
            user_id=user_id,
            image_hash=f"hash-{request_id}",
            preset_id="instagram",
            instruction_hash=f"instruction-{request_id}",
            prompt_version="prompt-v-test",
            model="model-test",
            original_path=None,
            prompt=None,
        )
        await crud.mark_generation_success(
            db,
            request_id=request_id,
            output_path=output_path,
            image_url=None,
        )


def test_create_download_url_returns_r2_signed_url(monkeypatch) -> None:
    class FakeStorage:
        async def download_url(
            self,
            path: str,
            *,
            filename: str,
            content_type: str,
            expires_in: int,
        ) -> str:
            assert path == "outputs/result.png"
            assert filename == "result.png"
            assert content_type == "image/png"
            assert expires_in == 1800
            return "https://signed.example/result.png"

    async def _override_user() -> AuthUser:
        return _user("download-owner")

    asyncio.run(
        _seed_success_generation(
            request_id="download-r2",
            user_id="download-owner",
            output_path="outputs/result.png",
        )
    )
    monkeypatch.setattr("backend.app.api.assets.get_storage", lambda settings: FakeStorage())
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.post("/api/assets/generations/download-r2/download-url")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json() == {
        "downloadUrl": "https://signed.example/result.png",
        "expiresIn": 1800,
    }


def test_create_download_url_is_user_scoped() -> None:
    async def _other_user() -> AuthUser:
        return _user("download-other")

    asyncio.run(
        _seed_success_generation(
            request_id="download-owned",
            user_id="download-owner",
            output_path="outputs/result.png",
        )
    )
    app.dependency_overrides[get_current_user] = _other_user
    try:
        response = client.post("/api/assets/generations/download-owned/download-url")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 404


def test_local_download_returns_attachment(tmp_path: Path) -> None:
    output_path = tmp_path / "result.png"
    output_path.write_bytes(b"image-bytes")

    async def _override_user() -> AuthUser:
        return _user("download-local")

    asyncio.run(
        _seed_success_generation(
            request_id="download-local",
            user_id="download-local",
            output_path=str(output_path),
        )
    )
    app.dependency_overrides[get_current_user] = _override_user
    try:
        response = client.get("/api/assets/generations/download-local/download")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.content == b"image-bytes"
    assert response.headers["content-disposition"].startswith("attachment;")
