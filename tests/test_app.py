from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import (
    _cors_headers,
    _cors_methods,
    _docs_urls,
    _should_mount_static_assets,
    app,
)

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready() -> None:
    response = client.get("/api/ready")
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "ready"
    assert body["presets"] == 3


def test_docs_are_disabled_in_production() -> None:
    settings = Settings(app_env="production", database_url="sqlite:///tmp/app.db")

    assert _docs_urls(settings) == {
        "docs_url": None,
        "redoc_url": None,
        "openapi_url": None,
    }


def test_production_uses_restricted_cors_settings() -> None:
    settings = Settings(app_env="production", database_url="sqlite:///tmp/app.db")

    assert _cors_methods(settings) == ["GET", "POST", "PATCH", "DELETE"]
    assert _cors_headers(settings) == ["Authorization", "Content-Type", "X-Request-ID"]


def test_static_mounts_are_disabled_in_production() -> None:
    settings = Settings(app_env="production", database_url="sqlite:///tmp/app.db")

    assert _should_mount_static_assets(settings) is False
