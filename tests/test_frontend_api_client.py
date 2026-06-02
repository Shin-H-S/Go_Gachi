import base64
from types import SimpleNamespace

import pytest

from frontend import api_client


class FakeResponse:
    def __init__(self, payload: dict[str, str]) -> None:
        self.payload = payload
        self.raise_for_status_called = False

    def raise_for_status(self) -> None:
        self.raise_for_status_called = True

    def json(self) -> dict[str, str]:
        return self.payload


def test_request_backend_sends_expected_generate_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_request = {}
    result_data_url = "data:image/png;base64,cmVzdWx0LWltYWdl"

    def fake_post(url: str, json: dict[str, str], timeout: int) -> FakeResponse:
        captured_request.update(
            {
                "url": url,
                "json": json,
                "timeout": timeout,
            }
        )
        return FakeResponse({"imageDataUrl": result_data_url})

    uploaded_file = SimpleNamespace(
        type="image/png",
        getvalue=lambda: b"source-image",
    )
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    result = api_client.request_backend(
        uploaded_file,
        "  제품을 크게 보여줘  ",
        "인스타그램",
        "정사각형 피드",
    )

    assert result == b"result-image"
    assert captured_request == {
        "url": "https://backend.example/api/generate",
        "json": {
            "imageDataUrl": (
                "data:image/png;base64,"
                f"{base64.b64encode(b'source-image').decode('ascii')}"
            ),
            "presetId": "instagram_square",
            "detailType": "square_feed",
            "feedback": "광고 유형: 정사각형 피드\n제품을 크게 보여줘",
            "targetWidth": 1080,
            "targetHeight": 1080,
        },
        "timeout": 120,
    }


def test_request_backend_uses_default_local_backend_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_request = {}

    def fake_post(url: str, json: dict[str, object], timeout: int) -> FakeResponse:  # noqa: ARG001
        captured_request["url"] = url
        return FakeResponse({"imageDataUrl": "data:image/png;base64,cmVzdWx0"})

    uploaded_file = SimpleNamespace(
        type="image/png",
        getvalue=lambda: b"source-image",
    )
    monkeypatch.setattr(api_client, "BACKEND_URL", api_client.DEFAULT_BACKEND_URL)
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    api_client.request_backend(
        uploaded_file,
        "제품을 크게 보여줘",
        "인스타그램",
        "정사각형 피드",
    )

    assert captured_request["url"] == "http://127.0.0.1:8080/api/generate"


def test_request_backend_rejects_missing_image_data_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(url: str, json: dict[str, str], timeout: int) -> FakeResponse:  # noqa: ARG001
        return FakeResponse({})

    uploaded_file = SimpleNamespace(
        type="image/png",
        getvalue=lambda: b"source-image",
    )
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    with pytest.raises(ValueError, match="imageDataUrl"):
        api_client.request_backend(
            uploaded_file,
            "제품을 크게 보여줘",
            "인스타그램",
            "정사각형 피드",
        )


def test_file_to_data_url_defaults_to_application_octet_stream() -> None:
    uploaded_file = SimpleNamespace(
        type="",
        getvalue=lambda: b"raw-bytes",
    )

    assert (
        api_client.file_to_data_url(uploaded_file)
        == "data:application/octet-stream;base64,cmF3LWJ5dGVz"
    )
