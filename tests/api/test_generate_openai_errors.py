import base64

import httpx
import pytest

from backend.app.main import IMAGE_GENERATION_UNAVAILABLE_MESSAGE
from backend.app.services import generation_service, openai_images
from tests.api.helpers import TINY_PNG_DATA_URL, client, force_openai_mode


def test_generate_returns_503_when_openai_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    force_openai_mode(monkeypatch, api_key="")

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "userPrompt": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_generate_returns_503_when_provider_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        raise RuntimeError("provider exploded")

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "userPrompt": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_generate_returns_503_when_network_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BoomClient:
        def __init__(self, *args, **kwargs):  # noqa: ARG002, ANN003
            pass

        async def __aenter__(self):  # noqa: ANN202
            return self

        async def __aexit__(self, *args):  # noqa: ANN003, ANN202
            return None

        async def post(self, *args, **kwargs):  # noqa: ANN003, ARG002, ANN202
            raise httpx.ConnectError("network down")

    monkeypatch.setattr(openai_images.httpx, "AsyncClient", _BoomClient)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "userPrompt": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_generate_returns_503_when_openai_result_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _EmptyDataResponse:
        status_code = 200

        def json(self) -> dict[str, list[dict[str, str]]]:
            return {"data": []}

    class _EmptyDataClient:
        def __init__(self, *args, **kwargs):  # noqa: ARG002, ANN003
            pass

        async def __aenter__(self):  # noqa: ANN202
            return self

        async def __aexit__(self, *args):  # noqa: ANN003, ANN202
            return None

        async def post(self, *args, **kwargs):  # noqa: ANN003, ARG002, ANN202
            return _EmptyDataResponse()

    monkeypatch.setattr(openai_images.httpx, "AsyncClient", _EmptyDataClient)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "userPrompt": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_generate_returns_503_when_openai_result_base64_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return "not-valid-base64!"

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "userPrompt": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE


def test_generate_returns_503_when_openai_result_is_not_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_b64 = base64.b64encode(b"not-an-image").decode("ascii")

    async def _fake_call(**kwargs):  # noqa: ANN003, ANN202
        return fake_b64

    monkeypatch.setattr(generation_service, "call_openai_edit", _fake_call)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "userPrompt": ""},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == IMAGE_GENERATION_UNAVAILABLE_MESSAGE
