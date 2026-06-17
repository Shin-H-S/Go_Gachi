import httpx
import streamlit as st

from frontend.services.api_client import (
    BACKEND_URL,
    request_backend,
)
from frontend.services.backend_errors import format_backend_http_error
from frontend.services.generation_job_requests import request_backend_job
from frontend.work.job_notifications import (
    ACTIVE_GENERATION_JOBS_KEY,
    queue_generation_toast,
)
from frontend.work.state import append_result_to_history


def handle_generation_request(
    *,
    generate,
    uploaded_file,
    prompt: str,
    ad_copy_prompt: str,
    format_label: str,
    detail_label: str,
    current_result_context,
    ad_copy_enabled: bool,
    copy_mode: str,
) -> None:
    if generate:
        if not uploaded_file:
            st.warning("메뉴 사진을 먼저 업로드해주세요.")
        else:
            try:
                access_token = st.session_state.get("auth_access_token", "")
                result_context = dict(current_result_context or {})
                if access_token:
                    job = request_backend_job(
                        uploaded_file,
                        prompt.strip(),
                        format_label,
                        detail_label,
                        access_token=access_token,
                        ad_copy_enabled=ad_copy_enabled,
                        copy_mode=copy_mode,
                        ad_copy_prompt=ad_copy_prompt,
                    )
                    request_id = str(job.get("requestId") or job.get("jobId") or "")
                    if not request_id:
                        raise ValueError("백엔드 job 응답에 requestId가 없습니다.")
                    active_jobs = dict(st.session_state.get(ACTIVE_GENERATION_JOBS_KEY) or {})
                    active_jobs[request_id] = {
                        "requestId": request_id,
                        "status": job.get("status") or "pending",
                        "context": result_context,
                        "format_label": format_label,
                        "detail_label": detail_label,
                    }
                    st.session_state[ACTIVE_GENERATION_JOBS_KEY] = active_jobs
                    queue_generation_toast(
                        "이미지 생성을 시작했어요. 완료되면 알려드릴게요.",
                        session_state=st.session_state,
                    )
                    st.rerun()
                    return

                result = request_backend(
                    uploaded_file,
                    prompt.strip(),
                    format_label,
                    detail_label,
                    access_token=access_token,
                    ad_copy_enabled=ad_copy_enabled,
                    copy_mode=copy_mode,
                    ad_copy_prompt=ad_copy_prompt,
                )

                # 같은 원본 안에서 생성 결과를 누적해 화살표로 탐색할 수 있게 한다.
                st.session_state["result_history_upload"] = result_context.get("uploadHash")
                append_result_to_history(
                    {
                        "bytes": result.image_bytes,
                        "url": result.image_url,
                        "copy": result.copy,
                        "context": result_context,
                        "format_label": format_label,
                        "detail_label": detail_label,
                    },
                    session_state=st.session_state,
                )
                st.rerun()
            except httpx.HTTPStatusError as exc:
                st.error(
                    format_backend_http_error(
                        exc,
                        default_title="백엔드 생성 요청 실패",
                    )
                )
            except httpx.HTTPError as exc:
                st.error(
                    f"백엔드 연결 실패 [NETWORK_ERROR] {BACKEND_URL}: {type(exc).__name__}: {exc}"
                )
            except Exception as exc:
                st.error(f"이미지 생성 중 오류가 발생했습니다: {exc}")
