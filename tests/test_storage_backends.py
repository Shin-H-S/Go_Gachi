from typing import Any

import pytest

from backend.app.core.config import get_settings
from backend.app.services.storage.local import LocalStorage
from backend.app.services.storage.r2 import R2Storage

pytestmark = pytest.mark.anyio


class FakeS3Client:
    def __init__(self) -> None:
        self.presign_calls = 0

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
        self.presign_calls += 1
        assert ClientMethod == "get_object"
        assert Params["Bucket"] == "bucket"
        assert Params["ResponseContentDisposition"].startswith("attachment;")
        assert ExpiresIn == 300
        return f"https://signed.example/{Params['Key']}"


class FakeSession:
    def __init__(self) -> None:
        self.client_calls = 0
        self.last_client: FakeS3Client | None = None

    def client(self, service_name: str, **kwargs: str) -> FakeS3Client:
        self.client_calls += 1
        assert service_name == "s3"
        assert kwargs["endpoint_url"] == "https://account.r2.cloudflarestorage.com"
        self.last_client = FakeS3Client()
        return self.last_client


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
    fake_session = FakeSession()
    monkeypatch.setattr("backend.app.services.storage.r2.aioboto3.Session", lambda: fake_session)

    storage = R2Storage(settings)

    url = await storage.download_url(
        "outputs/result.png",
        filename="result.png",
        content_type="image/png",
        expires_in=300,
    )

    assert url == "https://signed.example/outputs/result.png"


async def test_r2_download_urls_reuses_single_client(monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "r2_endpoint_url", "https://account.r2.cloudflarestorage.com")
    monkeypatch.setattr(settings, "r2_access_key_id", "access")
    monkeypatch.setattr(settings, "r2_secret_access_key", "secret")
    monkeypatch.setattr(settings, "r2_bucket_name", "bucket")
    fake_session = FakeSession()
    monkeypatch.setattr("backend.app.services.storage.r2.aioboto3.Session", lambda: fake_session)

    storage = R2Storage(settings)

    urls = await storage.download_urls(
        [
            {
                "path": "outputs/result-1.png",
                "filename": "result-1.png",
                "content_type": "image/png",
            },
            {
                "path": "outputs/result-2.png",
                "filename": "result-2.png",
                "content_type": "image/png",
            },
        ],
        expires_in=300,
    )

    assert urls == [
        "https://signed.example/outputs/result-1.png",
        "https://signed.example/outputs/result-2.png",
    ]
    assert fake_session.client_calls == 1
    assert fake_session.last_client is not None
    assert fake_session.last_client.presign_calls == 2
