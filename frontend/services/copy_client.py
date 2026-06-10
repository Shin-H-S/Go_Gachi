import httpx

from frontend.core.config import BACKEND_URL, FORMAT_OPTIONS, get_detail_id
from frontend.services.prompting import build_user_prompt


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"} if access_token else {}


def request_auto_copy(
    prompt: str,
    format_label: str,
    detail_label: str,
    *,
    copy_mode: str = "rewrite",
    access_token: str = "",
) -> dict[str, object]:
    payload = {
        "presetId": FORMAT_OPTIONS[format_label]["value"],
        "detailType": get_detail_id(format_label, detail_label),
        "userPrompt": build_user_prompt(prompt, detail_label),
        "copyMode": copy_mode,
    }

    response = httpx.post(
        f"{BACKEND_URL}/api/copy/generate",
        json=payload,
        headers=_auth_headers(access_token),
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    copy = data.get("copy") if isinstance(data.get("copy"), dict) else data
    if not isinstance(copy, dict):
        raise ValueError("백엔드 응답에 광고 문구 데이터가 없습니다.")
    return copy
