from dataclasses import dataclass

import httpx

from frontend.core.config import (
    BACKEND_URL,
    DEFAULT_BACKEND_URL,
    FORMAT_OPTIONS,
    get_detail_id,
    get_detail_size,
)
from frontend.services import mypage_client
from frontend.services.assets import (
    data_url_to_bytes,
    file_to_data_url,
    request_asset_bytes,
)
from frontend.services.copy_client import request_auto_copy
from frontend.services.generation_jobs_client import request_generate_job_bytes
from frontend.services.prompting import build_user_prompt

__all__ = [
    "BACKEND_URL",
    "DEFAULT_BACKEND_URL",
    "GenerationResult",
    "build_user_prompt",
    "create_my_folder",
    "data_url_to_bytes",
    "file_to_data_url",
    "move_generation_to_folder",
    "request_asset_bytes",
    "request_auto_copy",
    "request_me",
    "request_backend",
    "request_my_folders",
    "request_my_generations",
    "request_my_uploads",
    "to_backend_asset_url",
]


@dataclass(frozen=True)
class GenerationResult:
    image_bytes: bytes
    copy: dict[str, object] | None = None
    logo: dict[str, object] | None = None


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"} if access_token else {}


def _sync_mypage_backend_url() -> None:
    mypage_client.BACKEND_URL = BACKEND_URL


def request_me(access_token: str) -> dict:
    _sync_mypage_backend_url()
    return mypage_client.request_me(access_token)


def request_my_generations(access_token: str, page: int = 1) -> dict:
    _sync_mypage_backend_url()
    return mypage_client.request_my_generations(access_token, page)


def request_my_folders(access_token: str) -> dict:
    _sync_mypage_backend_url()
    return mypage_client.request_my_folders(access_token)


def request_my_uploads(access_token: str) -> dict:
    _sync_mypage_backend_url()
    return mypage_client.request_my_uploads(access_token)


def create_my_folder(access_token: str, name: str) -> dict:
    _sync_mypage_backend_url()
    return mypage_client.create_my_folder(access_token, name)


def move_generation_to_folder(
    access_token: str,
    request_id: str,
    folder_id: int | None,
) -> dict:
    _sync_mypage_backend_url()
    return mypage_client.move_generation_to_folder(access_token, request_id, folder_id)


def to_backend_asset_url(path: str | None) -> str | None:
    if not path:
        return None
    if path.startswith(("http://", "https://", "data:")):
        return path
    if path.startswith("/"):
        return f"{BACKEND_URL.rstrip('/')}{path}"
    return f"{BACKEND_URL.rstrip('/')}/{path}"


def _build_generate_payload(
    uploaded_file,
    prompt: str,
    format_label: str,
    detail_label: str,
    ad_copy_enabled: bool,
    copy_mode: str,
    ad_copy_prompt: str,
    logo_file,
    logo_position: str,
) -> dict[str, object]:
    target_size = get_detail_size(format_label, detail_label)
    user_copy = ad_copy_prompt.strip() if ad_copy_enabled else ""
    return {
        "imageDataUrl": file_to_data_url(uploaded_file),
        "presetId": FORMAT_OPTIONS[format_label]["value"],
        "detailType": get_detail_id(format_label, detail_label),
        "userPrompt": build_user_prompt(prompt, detail_label),
        "userCopy": user_copy,
        "copyMode": copy_mode,
        "adCopyEnabled": ad_copy_enabled,
        "logoDataUrl": file_to_data_url(logo_file) if logo_file is not None else None,
        "logoPosition": logo_position,
        "targetWidth": target_size[0],
        "targetHeight": target_size[1],
    }


def _request_generate_sync(payload: dict[str, object], access_token: str) -> GenerationResult:
    response = httpx.post(
        f"{BACKEND_URL}/api/generate",
        json=payload,
        headers=_auth_headers(access_token),
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    image_data_url = data.get("imageDataUrl")
    if not image_data_url:
        raise ValueError("백엔드 응답에 imageDataUrl이 없습니다.")

    return GenerationResult(
        image_bytes=data_url_to_bytes(image_data_url),
        copy=data.get("copy"),
        logo=data.get("logo"),
    )


def _request_generate_job(payload: dict[str, object], access_token: str) -> GenerationResult:
    image_bytes, data = request_generate_job_bytes(payload, access_token)
    if image_bytes is None:
        image_data_url = data.get("imageDataUrl")
        if not image_data_url:
            raise ValueError("백엔드 job 응답에 imageUrl이 없습니다.")
        image_bytes = data_url_to_bytes(str(image_data_url))
    return GenerationResult(
        image_bytes=image_bytes,
        copy=data.get("copy") if isinstance(data.get("copy"), dict) else None,
        logo=data.get("logo") if isinstance(data.get("logo"), dict) else None,
    )


def request_backend(
    uploaded_file,
    prompt: str,
    format_label: str,
    detail_label: str,
    access_token: str = "",
    ad_copy_enabled: bool = True,
    copy_mode: str = "preserve",
    ad_copy_prompt: str = "",
    logo_file=None,
    logo_position: str = "bottom_right",
) -> GenerationResult:
    payload = _build_generate_payload(
        uploaded_file,
        prompt,
        format_label,
        detail_label,
        ad_copy_enabled,
        copy_mode,
        ad_copy_prompt,
        logo_file,
        logo_position,
    )

    if access_token:
        return _request_generate_job(payload, access_token)
    return _request_generate_sync(payload, access_token)
