import base64

import httpx

from frontend.core.config import BACKEND_URL


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
