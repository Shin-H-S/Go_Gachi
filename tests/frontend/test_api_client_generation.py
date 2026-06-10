import base64
from types import SimpleNamespace

import pytest

from frontend import api_client


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def test_request_backend_sends_expected_generate_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_request = {}
    result_data_url = "data:image/png;base64,cmVzdWx0LWltYWdl"

    def fake_post(
        url: str,
        json: dict[str, object],
        headers: dict[str, str],
        timeout: int,
    ) -> FakeResponse:
        captured_request.update(
            {"url": url, "json": json, "headers": headers, "timeout": timeout}
        )
        return FakeResponse({"imageDataUrl": result_data_url})

    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    result = api_client.request_backend(
        uploaded_file,
        "  제품이 크게 보여요  ",
        "인스타그램",
        "정사각형 피드",
    )

    assert result.image_bytes == b"result-image"
    assert result.copy is None
    assert captured_request == {
        "url": "https://backend.example/api/generate",
        "json": {
            "imageDataUrl": (
                f"data:image/png;base64,{base64.b64encode(b'source-image').decode('ascii')}"
            ),
            "presetId": "instagram",
            "detailType": "square_feed",
            "userPrompt": (
                "광고 유형: 정사각형 피드\n\n"
                "이미지 요청:\n제품이 크게 보여요"
            ),
            "userCopy": "",
            "copyMode": "preserve",
            "textOverlayEnabled": True,
            "logoDataUrl": None,
            "logoPosition": "bottom_right",
            "targetWidth": 1080,
            "targetHeight": 1080,
        },
        "headers": {},
        "timeout": 300,
    }


def test_request_backend_attaches_authorization_header_when_token_given(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_headers: dict[str, str] = {}

    def fake_post(
        url: str,  # noqa: ARG001
        json: dict[str, object],  # noqa: ARG001
        headers: dict[str, str],
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        captured_headers.update(headers)
        return FakeResponse({"imageDataUrl": "data:image/png;base64,cmVzdWx0"})

    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    api_client.request_backend(
        uploaded_file,
        "프롬프트",
        "인스타그램",
        "정사각형 피드",
        access_token="fake-jwt-token",
    )

    assert captured_headers == {"Authorization": "Bearer fake-jwt-token"}


def test_request_backend_sends_copy_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_json: dict[str, object] = {}

    def fake_post(
        url: str,  # noqa: ARG001
        json: dict[str, object],
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        captured_json.update(json)
        return FakeResponse({"imageDataUrl": "data:image/png;base64,cmVzdWx0"})

    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    api_client.request_backend(
        uploaded_file,
        "따뜻한 카페 분위기로",
        "인스타그램",
        "정사각형 피드",
        copy_mode="polish",
        ad_copy_prompt="오늘만 할인",
    )

    assert captured_json["copyMode"] == "polish"
    assert captured_json["userCopy"] == "오늘만 할인"


def test_request_backend_sends_logo_data_url_when_logo_uploaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_json: dict[str, object] = {}

    def fake_post(
        url: str,  # noqa: ARG001
        json: dict[str, object],
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        captured_json.update(json)
        return FakeResponse({"imageDataUrl": "data:image/png;base64,cmVzdWx0"})

    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    logo_file = SimpleNamespace(type="image/png", getvalue=lambda: b"logo-image")
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    api_client.request_backend(
        uploaded_file,
        "따뜻한 배경으로",
        "인스타그램",
        "정사각형 피드",
        logo_file=logo_file,
    )

    assert captured_json["logoDataUrl"] == (
        f"data:image/png;base64,{base64.b64encode(b'logo-image').decode('ascii')}"
    )
    assert captured_json["logoPosition"] == "bottom_right"


def test_request_backend_sends_null_logo_data_url_without_logo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_json: dict[str, object] = {}

    def fake_post(
        url: str,  # noqa: ARG001
        json: dict[str, object],
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        captured_json.update(json)
        return FakeResponse({"imageDataUrl": "data:image/png;base64,cmVzdWx0"})

    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    api_client.request_backend(
        uploaded_file,
        "따뜻한 배경으로",
        "인스타그램",
        "정사각형 피드",
    )

    assert captured_json["logoDataUrl"] is None


def test_request_backend_sends_image_prompt_and_user_copy_separately(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_json: dict[str, object] = {}

    def fake_post(
        url: str,  # noqa: ARG001
        json: dict[str, object],
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        captured_json.update(json)
        return FakeResponse({"imageDataUrl": "data:image/png;base64,cmVzdWx0"})

    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    api_client.request_backend(
        uploaded_file,
        "따뜻한 배경으로",
        "인스타그램",
        "정사각형 피드",
        ad_copy_prompt="헤드라인: 오늘만 할인",
        copy_mode="polish",
    )

    assert captured_json["userPrompt"] == (
        "광고 유형: 정사각형 피드\n\n"
        "이미지 요청:\n따뜻한 배경으로"
    )
    assert captured_json["userCopy"] == "헤드라인: 오늘만 할인"


def test_request_backend_keeps_user_copy_empty_when_text_overlay_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_json: dict[str, object] = {}

    def fake_post(
        url: str,  # noqa: ARG001
        json: dict[str, object],
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        captured_json.update(json)
        return FakeResponse({"imageDataUrl": "data:image/png;base64,cmVzdWx0"})

    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    api_client.request_backend(
        uploaded_file,
        "텍스트 없는 이미지로",
        "인스타그램",
        "정사각형 피드",
        ad_copy_prompt="이미지에 들어가면 안 되는 문구",
        text_overlay_enabled=False,
    )

    assert captured_json["textOverlayEnabled"] is False
    assert captured_json["userCopy"] == ""


def test_request_backend_returns_copy_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    copy_payload = {
        "headline": "오늘 아메리카노 2,500원",
        "subcopy": "카페에서 더 맛있게 즐겨보세요.",
        "cta": None,
        "copyMode": "polish",
    }

    def fake_post(
        url: str,  # noqa: ARG001
        json: dict[str, object],  # noqa: ARG001
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        return FakeResponse(
            {
                "imageDataUrl": "data:image/png;base64,cmVzdWx0",
                "copy": copy_payload,
            }
        )

    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    result = api_client.request_backend(
        uploaded_file,
        "따뜻한 카페 분위기로",
        "인스타그램",
        "정사각형 피드",
        ad_copy_prompt="오늘 아메리카노 2,500원",
        copy_mode="polish",
    )

    assert result.image_bytes == b"result"
    assert result.copy == copy_payload


def test_request_backend_uses_default_local_backend_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_request = {}

    def fake_post(
        url: str,
        json: dict[str, object],  # noqa: ARG001
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        captured_request["url"] = url
        return FakeResponse({"imageDataUrl": "data:image/png;base64,cmVzdWx0"})

    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    monkeypatch.setattr(api_client, "BACKEND_URL", api_client.DEFAULT_BACKEND_URL)
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    api_client.request_backend(uploaded_file, "제품이 크게 보여요", "인스타그램", "정사각형 피드")

    assert captured_request["url"] == "http://127.0.0.1:8080/api/generate"


def test_request_backend_rejects_missing_image_data_url(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(
        url: str,  # noqa: ARG001
        json: dict[str, str],  # noqa: ARG001
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        return FakeResponse({})

    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    with pytest.raises(ValueError, match="imageDataUrl"):
        api_client.request_backend(
            uploaded_file,
            "제품이 크게 보여요",
            "인스타그램",
            "정사각형 피드",
        )


def test_file_to_data_url_defaults_to_application_octet_stream() -> None:
    uploaded_file = SimpleNamespace(type="", getvalue=lambda: b"raw-bytes")

    assert (
        api_client.file_to_data_url(uploaded_file)
        == "data:application/octet-stream;base64,cmF3LWJ5dGVz"
    )
