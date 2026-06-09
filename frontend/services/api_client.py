import base64

import httpx

from frontend.core.config import (
    BACKEND_URL,
    DEFAULT_BACKEND_URL,
    FORMAT_OPTIONS,
    FRONTEND_USE_MOCK,
    get_detail_id,
    get_detail_size,
)

__all__ = [
    "BACKEND_URL",
    "DEFAULT_BACKEND_URL",
    "FRONTEND_USE_MOCK",
    "build_user_prompt",
    "create_my_folder",
    "data_url_to_bytes",
    "file_to_data_url",
    "move_generation_to_folder",
    "request_asset_bytes",
    "request_me",
    "request_backend",
    "request_my_folders",
    "request_my_generations",
    "request_my_uploads",
    "to_backend_asset_url",
]


def file_to_data_url(uploaded_file) -> str:
    mime_type = uploaded_file.type or "application/octet-stream"
    encoded = base64.b64encode(uploaded_file.getvalue()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def data_url_to_bytes(data_url: str) -> bytes:
    if "," not in data_url:
        raise ValueError("백엔드 응답 imageDataUrl 형식이 올바르지 않습니다.")

    header, encoded = data_url.split(",", 1)
    if ";base64" not in header:
        raise ValueError("백엔드 응답 imageDataUrl은 base64 데이터 URL이어야 합니다.")

    return base64.b64decode(encoded)


def build_user_prompt(prompt: str, detail_label: str) -> str:
    return f"광고 유형: {detail_label}\n{prompt.strip()}"


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"} if access_token else {}


def _get_json(path: str, access_token: str, timeout: int = 30) -> dict:
    response = httpx.get(
        f"{BACKEND_URL}{path}",
        headers=_auth_headers(access_token),
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def request_me(access_token: str) -> dict:
    return _get_json("/api/auth/me", access_token)


def request_my_generations(access_token: str) -> dict:
    return _get_json("/api/auth/me/generations", access_token)


def request_my_folders(access_token: str) -> dict:
    return _get_json("/api/auth/me/folders", access_token)


def request_my_uploads(access_token: str) -> dict:
    return _get_json("/api/auth/me/uploads", access_token)


def create_my_folder(access_token: str, name: str) -> dict:
    response = httpx.post(
        f"{BACKEND_URL}/api/auth/me/folders",
        json={"name": name},
        headers=_auth_headers(access_token),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def move_generation_to_folder(
    access_token: str,
    request_id: str,
    folder_id: int | None,
) -> dict:
    response = httpx.patch(
        f"{BACKEND_URL}/api/auth/me/generations/{request_id}/folder",
        json={"folder_id": folder_id},
        headers=_auth_headers(access_token),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def to_backend_asset_url(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith(("http://", "https://", "data:")):
        return path
    if path.startswith("/"):
        return f"{BACKEND_URL.rstrip('/')}{path}"
    return f"{BACKEND_URL.rstrip('/')}/{path}"


def request_asset_bytes(url: str) -> bytes:
    if url.startswith("data:"):
        return data_url_to_bytes(url)

    response = httpx.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def request_backend(
    uploaded_file,
    prompt: str,
    format_label: str,
    detail_label: str,
    access_token: str = "",
) -> bytes:
    target_size = get_detail_size(format_label, detail_label)
    payload = {
        "imageDataUrl": file_to_data_url(uploaded_file),
        "presetId": FORMAT_OPTIONS[format_label]["value"],
        "detailType": get_detail_id(format_label, detail_label),
        "userPrompt": build_user_prompt(prompt, detail_label),
        "targetWidth": target_size[0],
        "targetHeight": target_size[1],
    }

    # 로그인 상태면 JWT를 Authorization 헤더에 담아 백엔드로 전달한다.
    # 비로그인이면 빈 headers를 보내고, 백엔드는 익명 요청(user_id=None)으로 처리한다.
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    response = httpx.post(
        f"{BACKEND_URL}/api/generate",
        json=payload,
        headers=headers,
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    image_data_url = data.get("imageDataUrl")
    if not image_data_url:
        raise ValueError("백엔드 응답에 imageDataUrl이 없습니다.")

    return data_url_to_bytes(image_data_url)
