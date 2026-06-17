import httpx
import streamlit as st

from frontend.services.generation_jobs_client import get_generation_job_status
from frontend.work.state import append_result_to_history

DONE_STATUSES = {"success", "cached"}
WAITING_STATUSES = {"pending", "processing", "done"}


def _toast(message: str) -> None:
    """Streamlit 버전에 따라 toast가 없을 수 있어 안전하게 호출한다."""
    if hasattr(st, "toast"):
        st.toast(message)


def _active_jobs() -> dict[str, dict[str, object]]:
    jobs = st.session_state.get("active_generation_jobs")
    return jobs if isinstance(jobs, dict) else {}


def process_generation_job_notifications() -> None:
    """앱 내부 이동 중 완료된 이미지 생성 job을 확인해 알림과 결과를 반영한다."""
    access_token = st.session_state.get("auth_access_token", "")
    if not access_token:
        return

    jobs = dict(_active_jobs())
    if not jobs:
        return

    changed = False
    for request_id, job in list(jobs.items()):
        try:
            data = get_generation_job_status(request_id, str(access_token))
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                jobs.pop(request_id, None)
                changed = True
            continue
        except httpx.HTTPError:
            continue

        status = str(data.get("status") or job.get("status") or "pending")
        job["status"] = status
        if status in WAITING_STATUSES:
            jobs[request_id] = job
            changed = True
            continue

        if status in DONE_STATUSES:
            image_url = data.get("imageUrl")
            if not image_url:
                jobs[request_id] = job
                changed = True
                continue

            context = job.get("context") if isinstance(job.get("context"), dict) else {}
            st.session_state["result_history_upload"] = context.get("uploadHash")
            append_result_to_history(
                {
                    "bytes": None,
                    "url": str(image_url),
                    "copy": data.get("copy") if isinstance(data.get("copy"), dict) else None,
                    "context": context,
                    "format_label": job.get("format_label"),
                    "detail_label": job.get("detail_label"),
                },
                session_state=st.session_state,
            )
            jobs.pop(request_id, None)
            changed = True
            _toast("이미지 생성이 완료됐어요.")
            continue

        if status == "failed":
            jobs.pop(request_id, None)
            changed = True
            _toast(f"이미지 생성에 실패했어요: {data.get('error') or 'GENERATION_JOB_FAILED'}")

    if changed:
        st.session_state["active_generation_jobs"] = jobs
