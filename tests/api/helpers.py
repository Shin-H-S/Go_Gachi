import base64
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.core.config import Settings, get_settings
from backend.app.main import app

TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhg"
    "GAWjR9awAAAABJRU5ErkJggg=="
)
TINY_PNG_DATA_URL = f"data:image/png;base64,{TINY_PNG_B64}"

client = TestClient(app)


def image_size_from_data_url(data_url: str) -> tuple[int, int]:
    _, encoded = data_url.split(",", 1)
    with Image.open(BytesIO(base64.b64decode(encoded))) as image:
        return image.size


def force_openai_mode(
    monkeypatch: pytest.MonkeyPatch,
    *,
    api_key: str = "test-key",
) -> Settings:
    real_settings = get_settings()
    monkeypatch.setattr(real_settings, "image_provider", "openai")
    monkeypatch.setattr(real_settings, "openai_api_key", api_key)
    # 테스트는 디스크 기반 동작을 가정하므로 storage_backend를 local로 고정한다.
    monkeypatch.setattr(real_settings, "storage_backend", "local")
    return real_settings
