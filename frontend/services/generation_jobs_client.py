import time

import httpx

from frontend.core.config import BACKEND_URL
from frontend.services.assets import to_backend_asset_url


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"} if access_token else {}


def request_generate_job_result(
    payload: dict[str, object],
    access_token: str,
) -> dict[str, object]:
    create_response = httpx.post(
        f"{BACKEND_URL}/api/generate/jobs",
        json=payload,
        headers=_auth_headers(access_token),
        timeout=30,
    )
    create_response.raise_for_status()
    create_data = create_response.json()
    request_id = create_data.get("requestId")
    if not request_id:
        return create_data

    deadline = time.monotonic() + 300
    last_status = "pending"
    while time.monotonic() < deadline:
        time.sleep(2)
        status_response = httpx.get(
            f"{BACKEND_URL}/api/generate/jobs/{request_id}",
            headers=_auth_headers(access_token),
            timeout=30,
        )
        status_response.raise_for_status()
        data = status_response.json()
        last_status = data.get("status") or last_status

        if last_status in {"success", "cached"}:
            image_url = data.get("imageUrl")
            asset_url = to_backend_asset_url(str(image_url) if image_url else None)
            if not asset_url:
                raise ValueError("백엔드 job 응답에 imageUrl 또는 imageDataUrl이 없습니다.")
            data["imageUrl"] = asset_url
            return data

        if last_status == "failed":
            error = data.get("error") or "GENERATION_JOB_FAILED"
            raise ValueError(f"이미지 생성 job이 실패했습니다: {error}")

    raise TimeoutError(f"이미지 생성 job이 제한 시간 안에 끝나지 않았습니다: {last_status}")
