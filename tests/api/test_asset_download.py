from backend.app.core.config import get_settings
from tests.api.helpers import client


def test_download_output_asset_returns_attachment() -> None:
    settings = get_settings()
    output_file = settings.output_dir / "download-result.png"
    output_file.write_bytes(b"png")

    response = client.get("/api/assets/download/outputs/download-result.png")

    assert response.status_code == 200
    assert response.content == b"png"
    assert response.headers["content-type"] == "image/png"
    assert "attachment" in response.headers["content-disposition"]
    assert "download-result.png" in response.headers["content-disposition"]


def test_download_asset_rejects_path_traversal() -> None:
    response = client.get("/api/assets/download/outputs/../secret.png")

    assert response.status_code in {400, 404}


def test_download_asset_returns_404_when_missing() -> None:
    response = client.get("/api/assets/download/outputs/missing-result.png")

    assert response.status_code == 404
