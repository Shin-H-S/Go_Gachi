import base64

import httpx
import pytest

from backend.app import main as app_main
from backend.app.core.errors import ServiceError
from backend.app.services import generation_service, openai_copy, openai_images
from tests.api.helpers import TINY_PNG_DATA_URL, client, force_openai_mode


def _assert_error_code(response, code: str) -> None:  # noqa: ANN001
    detail = response.json()["detail"]
    assert detail["code"] == code
    assert detail["message"]


def test_generate_returns_503_when_openai_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    force_openai_mode(monkeypatch, api_key="")

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "userPrompt": ""},
    )

    assert response.status_code == 503
    _assert_error_code(response, "OPENAI_API_KEY_MISSING")


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
    _assert_error_code(response, "IMAGE_API_CALL_FAILED")


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
    _assert_error_code(response, "IMAGE_API_CONNECTION_FAILED")


def test_generate_returns_timeout_code_when_image_api_times_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _TimeoutClient:
        def __init__(self, *args, **kwargs):  # noqa: ARG002, ANN003
            pass

        async def __aenter__(self):  # noqa: ANN202
            return self

        async def __aexit__(self, *args):  # noqa: ANN003, ANN202
            return None

        async def post(self, *args, **kwargs):  # noqa: ANN003, ARG002, ANN202
            raise httpx.ReadTimeout("image timeout")

    monkeypatch.setattr(openai_images.httpx, "AsyncClient", _TimeoutClient)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/generate",
        json={"imageDataUrl": TINY_PNG_DATA_URL, "presetId": None, "userPrompt": ""},
    )

    assert response.status_code == 503
    _assert_error_code(response, "IMAGE_API_TIMEOUT")


def test_generate_returns_503_when_openai_result_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _EmptyDataResponse:
        status_code = 200
        headers: dict[str, str] = {}

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
    _assert_error_code(response, "IMAGE_API_RESULT_EMPTY")


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
    _assert_error_code(response, "IMAGE_RESULT_DECODE_FAILED")


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
    _assert_error_code(response, "IMAGE_RESULT_PROCESS_FAILED")


def test_copy_generate_returns_service_error_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_copy(**kwargs):  # noqa: ANN003, ANN202
        raise ServiceError("COPY_API_CONNECTION_FAILED", "문구 생성 API에 연결하지 못했습니다.")

    monkeypatch.setattr(app_main, "generate_ad_copy", _fake_copy)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/copy/generate",
        json={
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "아메리카노 행사 문구",
            "copyMode": "rewrite",
        },
    )

    assert response.status_code == 503
    _assert_error_code(response, "COPY_API_CONNECTION_FAILED")


def test_copy_generate_returns_timeout_code_when_copy_api_times_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _TimeoutClient:
        def __init__(self, *args, **kwargs):  # noqa: ARG002, ANN003
            pass

        async def __aenter__(self):  # noqa: ANN202
            return self

        async def __aexit__(self, *args):  # noqa: ANN003, ANN202
            return None

        async def post(self, *args, **kwargs):  # noqa: ANN003, ARG002, ANN202
            raise httpx.ReadTimeout("copy timeout")

    monkeypatch.setattr(openai_copy.httpx, "AsyncClient", _TimeoutClient)
    force_openai_mode(monkeypatch)

    response = client.post(
        "/api/copy/generate",
        json={
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": "아메리카노 행사 문구",
            "copyMode": "rewrite",
        },
    )

    assert response.status_code == 503
    _assert_error_code(response, "COPY_API_TIMEOUT")
