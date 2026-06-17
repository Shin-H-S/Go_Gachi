from frontend.services.generation_jobs_client import create_generation_job
from frontend.services.generation_payload import build_generate_payload


def request_backend_job(
    uploaded_file,
    prompt: str,
    format_label: str,
    detail_label: str,
    access_token: str,
    ad_copy_enabled: bool = True,
    copy_mode: str = "preserve",
    ad_copy_prompt: str = "",
) -> dict[str, object]:
    """로그인 사용자의 이미지 생성 job을 시작하고 즉시 job 정보를 반환한다."""
    payload = build_generate_payload(
        uploaded_file,
        prompt,
        format_label,
        detail_label,
        ad_copy_enabled,
        copy_mode,
        ad_copy_prompt,
    )
    return create_generation_job(payload, access_token)
