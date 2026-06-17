import time

import httpx

from frontend.core.config import BACKEND_URL
from frontend.services.assets import to_backend_asset_url

JOB_DONE_STATUSES = {"success", "cached"}
LEGACY_JOB_POLL_INTERVAL_SECONDS = 5
LEGACY_JOB_TIMEOUT_SECONDS = 300


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"} if access_token else {}


def _is_backend_download_fallback(url: str, request_id: str) -> bool:
    expected = f"{BACKEND_URL.rstrip('/')}/api/assets/generations/{request_id}/download"
    return url == expected


def create_generation_job(payload: dict[str, object], access_token: str) -> dict[str, object]:
    """이미지 생성 job을 시작하고 즉시 식별자를 받는다."""
    create_response = httpx.post(
        f"{BACKEND_URL}/api/generate/jobs",
        json=payload,
        headers=_auth_headers(access_token),
        timeout=30,
    )
    create_response.raise_for_status()
    return create_response.json()


def create_generation_download_url(request_id: str, access_token: str) -> dict[str, object]:
    """생성 완료된 job 결과의 다운로드 URL을 발급받는다."""
    response = httpx.post(
        f"{BACKEND_URL}/api/assets/generations/{request_id}/download-url",
        headers=_auth_headers(access_token),
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    download_url = data.get("downloadUrl")
    if download_url:
        normalized_url = to_backend_asset_url(str(download_url))
        if normalized_url and not _is_backend_download_fallback(normalized_url, request_id):
            data["downloadUrl"] = normalized_url
        else:
            data["downloadUrl"] = None
    return data


def get_generation_job_status(request_id: str, access_token: str) -> dict[str, object]:
    """이미지 생성 job 상태를 조회하고 URL을 프론트에서 열 수 있게 보정한다."""
    status_response = httpx.get(
        f"{BACKEND_URL}/api/generate/jobs/{request_id}",
        headers=_auth_headers(access_token),
        timeout=30,
    )
    status_response.raise_for_status()
    data = status_response.json()
    image_url = data.get("imageUrl")
    if image_url:
        data["imageUrl"] = to_backend_asset_url(str(image_url))
    return data


def request_generate_job_result(
    payload: dict[str, object],
    access_token: str,
) -> dict[str, object]:
    create_data = create_generation_job(payload, access_token)
    request_id = create_data.get("requestId")
    if not request_id:
        return create_data

    deadline = time.monotonic() + LEGACY_JOB_TIMEOUT_SECONDS
    last_status = "pending"
    while time.monotonic() < deadline:
        # 현재 UI는 비동기 job polling을 사용한다.
        # 이 경로는 레거시 fallback이므로 호출 빈도를 낮춘다.
        time.sleep(LEGACY_JOB_POLL_INTERVAL_SECONDS)
        data = get_generation_job_status(str(request_id), access_token)
        last_status = data.get("status") or last_status

        if last_status in JOB_DONE_STATUSES:
            image_url = data.get("imageUrl")
            if not image_url:
                raise ValueError("백엔드 job 응답에 imageUrl 또는 imageDataUrl이 없습니다.")
            return data

        if last_status == "failed":
            error = data.get("error") or "GENERATION_JOB_FAILED"
            raise ValueError(f"이미지 생성 job이 실패했습니다: {error}")

    raise TimeoutError(f"이미지 생성 job이 제한 시간 안에 끝나지 않았습니다: {last_status}")
