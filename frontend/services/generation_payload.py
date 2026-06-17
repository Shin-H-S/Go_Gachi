from frontend.core.config import FORMAT_OPTIONS, get_detail_id, get_detail_size
from frontend.services.assets import file_to_data_url
from frontend.services.prompting import build_user_prompt


def build_generate_payload(
    uploaded_file,
    prompt: str,
    format_label: str,
    detail_label: str,
    ad_copy_enabled: bool,
    copy_mode: str,
    ad_copy_prompt: str,
) -> dict[str, object]:
    """프론트 입력값을 백엔드 /api/generate 요청 본문으로 변환한다."""
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
        "targetWidth": target_size[0],
        "targetHeight": target_size[1],
    }
