from typing import Any

import pytest

from backend.app.core.config import get_settings
from backend.app.services.storage.local import LocalStorage
from backend.app.services.storage.r2 import R2Storage

pytestmark = pytest.mark.anyio


class FakeS3Client:
    async def __aenter__(self) -> "FakeS3Client":
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def generate_presigned_url(
        self,
        ClientMethod: str,
        Params: dict[str, Any],
        ExpiresIn: int,
    ) -> str:
        assert ClientMethod == "get_object"
        assert Params["Bucket"] == "bucket"
        assert Params["Key"] == "outputs/result.png"
        assert Params["ResponseContentType"] == "image/png"
        assert Params["ResponseContentDisposition"].startswith("attachment;")
        assert ExpiresIn == 300
        return "https://signed.example/result.png"


class FakeSession:
    def client(self, service_name: str, **kwargs: str) -> FakeS3Client:
        assert service_name == "s3"
        assert kwargs["endpoint_url"] == "https://account.r2.cloudflarestorage.com"
        return FakeS3Client()


def test_r2_original_path_uses_generation_id(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "r2_public_url", "https://pub-test.r2.dev")

    storage = R2Storage(settings)

    assert (
        storage.original_path(
            image_hash="a" * 64,
            extension="png",
            generation_id="20260610_120000_abcdef",
        )
        == "uploads/20260610_120000_abcdef.png"
    )


def test_local_and_r2_original_path_use_same_filename_policy(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "upload_dir", settings.data_dir / "uploads")

    local_storage = LocalStorage(settings)
    r2_storage = R2Storage(settings)

    local_path = local_storage.original_path(
        image_hash="b" * 64,
        extension="jpg",
        generation_id="20260610_121000_abcdef",
    )
    r2_path = r2_storage.original_path(
        image_hash="b" * 64,
        extension="jpg",
        generation_id="20260610_121000_abcdef",
    )

    assert local_path.endswith("20260610_121000_abcdef.jpg")
    assert r2_path == "uploads/20260610_121000_abcdef.jpg"


async def test_r2_download_url_uses_presigned_get_object(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "r2_endpoint_url", "https://account.r2.cloudflarestorage.com")
    monkeypatch.setattr(settings, "r2_access_key_id", "access")
    monkeypatch.setattr(settings, "r2_secret_access_key", "secret")
    monkeypatch.setattr(settings, "r2_bucket_name", "bucket")
    monkeypatch.setattr("backend.app.services.storage.r2.aioboto3.Session", lambda: FakeSession())

    storage = R2Storage(settings)

    url = await storage.download_url(
        "outputs/result.png",
        filename="result.png",
        content_type="image/png",
        expires_in=300,
    )

    assert url == "https://signed.example/result.png"
