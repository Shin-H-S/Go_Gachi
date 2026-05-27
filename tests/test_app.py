from fastapi.testclient import TestClient

from backend.app.main import app

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
