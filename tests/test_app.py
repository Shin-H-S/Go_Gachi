from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import _docs_urls, app

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
