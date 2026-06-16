from frontend.services import api_client


def test_to_backend_asset_url_keeps_absolute_and_data_urls(
    monkeypatch,
) -> None:
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")

    assert api_client.to_backend_asset_url(None) is None
    assert api_client.to_backend_asset_url("data:image/png;base64,YWJj") == (
        "data:image/png;base64,YWJj"
    )
    assert api_client.to_backend_asset_url("https://cdn.example/image.png") == (
        "https://cdn.example/image.png"
    )


def test_to_backend_asset_url_normalizes_relative_backend_paths(
    monkeypatch,
) -> None:
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example/api-root")

    assert api_client.to_backend_asset_url("/outputs/result.png") == (
        "https://backend.example/api-root/outputs/result.png"
    )
    assert api_client.to_backend_asset_url("/uploads/original.png") == (
        "https://backend.example/api-root/uploads/original.png"
    )
    assert api_client.to_backend_asset_url("outputs/result.png") == (
        "https://backend.example/api-root/outputs/result.png"
    )
