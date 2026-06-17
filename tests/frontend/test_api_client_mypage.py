import pytest

from frontend.services import api_client


class FakeResponse:
    def __init__(self, payload: dict[str, object], content: bytes = b"") -> None:
        self.payload = payload
        self.content = content

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def test_mypage_get_requests_attach_authorization_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_requests: list[dict[str, object]] = []

    def fake_get(url: str, headers: dict[str, str], timeout: int) -> FakeResponse:
        captured_requests.append({"url": url, "headers": headers, "timeout": timeout})
        return FakeResponse({"items": [], "count": 0})

    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "get", fake_get)

    assert api_client.request_my_generations("jwt-token") == {"items": [], "count": 0}
    assert api_client.request_my_generations("jwt-token", page=2, uncategorized=True) == {
        "items": [],
        "count": 0,
    }
    assert api_client.request_my_folders("jwt-token") == {"items": [], "count": 0}
    assert api_client.request_my_uploads("jwt-token") == {"items": [], "count": 0}
    assert api_client.request_my_uploads("jwt-token", page=2) == {"items": [], "count": 0}

    assert captured_requests == [
        {
            "url": "https://backend.example/api/auth/me/generations",
            "headers": {"Authorization": "Bearer jwt-token"},
            "timeout": 30,
        },
        {
            "url": "https://backend.example/api/auth/me/generations?page=2&uncategorized=true",
            "headers": {"Authorization": "Bearer jwt-token"},
            "timeout": 30,
        },
        {
            "url": "https://backend.example/api/auth/me/folders",
            "headers": {"Authorization": "Bearer jwt-token"},
            "timeout": 30,
        },
        {
            "url": "https://backend.example/api/auth/me/uploads",
            "headers": {"Authorization": "Bearer jwt-token"},
            "timeout": 30,
        },
        {
            "url": "https://backend.example/api/auth/me/uploads?page=2",
            "headers": {"Authorization": "Bearer jwt-token"},
            "timeout": 30,
        },
    ]


def test_mypage_write_requests_send_expected_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_requests: list[dict[str, object]] = []

    def fake_post(
        url: str,
        json: dict[str, object],
        headers: dict[str, str],
        timeout: int,
    ) -> FakeResponse:
        captured_requests.append(
            {"method": "POST", "url": url, "json": json, "headers": headers, "timeout": timeout}
        )
        return FakeResponse({"id": 7, "name": "봄 신메뉴", "created_at": "now"})

    def fake_patch(
        url: str,
        json: dict[str, object],
        headers: dict[str, str],
        timeout: int,
    ) -> FakeResponse:
        captured_requests.append(
            {"method": "PATCH", "url": url, "json": json, "headers": headers, "timeout": timeout}
        )
        if url.endswith("/api/auth/me/folders/7"):
            return FakeResponse({"id": 7, "name": json["name"], "created_at": "now"})
        return FakeResponse({"request_id": "request-1", "folder_id": 7})

    def fake_delete(
        url: str,
        headers: dict[str, str],
        timeout: int,
    ) -> FakeResponse:
        captured_requests.append(
            {"method": "DELETE", "url": url, "headers": headers, "timeout": timeout}
        )
        return FakeResponse({})

    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)
    monkeypatch.setattr(api_client.httpx, "patch", fake_patch)
    monkeypatch.setattr(api_client.httpx, "delete", fake_delete)

    assert api_client.create_my_folder("jwt-token", "봄 신메뉴")["id"] == 7
    assert api_client.move_generation_to_folder("jwt-token", "request-1", 7)["folder_id"] == 7
    assert api_client.rename_my_folder("jwt-token", 7, "여름 신메뉴")["name"] == "여름 신메뉴"
    api_client.delete_my_folder("jwt-token", 7)

    assert captured_requests == [
        {
            "method": "POST",
            "url": "https://backend.example/api/auth/me/folders",
            "json": {"name": "봄 신메뉴"},
            "headers": {"Authorization": "Bearer jwt-token"},
            "timeout": 30,
        },
        {
            "method": "PATCH",
            "url": "https://backend.example/api/auth/me/generations/request-1/folder",
            "json": {"folder_id": 7},
            "headers": {"Authorization": "Bearer jwt-token"},
            "timeout": 30,
        },
        {
            "method": "PATCH",
            "url": "https://backend.example/api/auth/me/folders/7",
            "json": {"name": "여름 신메뉴"},
            "headers": {"Authorization": "Bearer jwt-token"},
            "timeout": 30,
        },
        {
            "method": "DELETE",
            "url": "https://backend.example/api/auth/me/folders/7",
            "headers": {"Authorization": "Bearer jwt-token"},
            "timeout": 30,
        },
    ]


def test_request_asset_bytes_reads_data_url_or_remote_bytes(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url: str, timeout: int) -> FakeResponse:
        captured.update({"url": url, "timeout": timeout})
        return FakeResponse({}, content=b"remote-image")

    monkeypatch.setattr(api_client.httpx, "get", fake_get)

    assert api_client.request_asset_bytes("data:image/png;base64,YWJj") == b"abc"
    assert api_client.request_asset_bytes("https://cdn.example/image.png") == b"remote-image"
    assert captured == {"url": "https://cdn.example/image.png", "timeout": 30}
