import httpx
import streamlit as st

from frontend.services.generation_jobs_client import get_generation_job_status
from frontend.work.state import append_result_to_history

DONE_STATUSES = {"success", "cached"}
WAITING_STATUSES = {"pending", "processing", "done"}
ACTIVE_GENERATION_JOBS_KEY = "active_generation_jobs"
GENERATION_TOASTS_KEY = "generation_toasts"


def active_generation_jobs(session_state=None) -> dict[str, dict[str, object]]:
    """현재 앱에서 추적 중인 이미지 생성 job 목록을 반환한다."""
    state = st.session_state if session_state is None else session_state
    jobs = state.get(ACTIVE_GENERATION_JOBS_KEY)
    return jobs if isinstance(jobs, dict) else {}


def has_active_generation_job(session_state=None) -> bool:
    """작업 페이지 로딩 패널을 유지할 active job이 있는지 확인한다."""
    return bool(active_generation_jobs(session_state))


def queue_generation_toast(message: str, session_state=None) -> None:
    """rerun 이후 표시할 알림 문구를 세션에 저장한다."""
    state = st.session_state if session_state is None else session_state
    toasts = list(state.get(GENERATION_TOASTS_KEY) or [])
    toasts.append(message)
    state[GENERATION_TOASTS_KEY] = toasts


def render_queued_generation_toasts() -> None:
    """이전 rerun에서 예약한 알림을 화면에 표시한다."""
    messages = list(st.session_state.pop(GENERATION_TOASTS_KEY, []) or [])
    if not hasattr(st, "toast"):
        return
    for message in messages:
        st.toast(str(message))


def process_generation_job_notifications() -> None:
    """앱 내부 이동 중 완료된 이미지 생성 job을 확인해 알림과 결과를 반영한다."""
    access_token = st.session_state.get("auth_access_token", "")
    if not access_token:
        return

    jobs = dict(active_generation_jobs())
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
            if hasattr(st, "toast"):
                st.toast("이미지 생성이 완료됐어요.")
            continue

        if status == "failed":
            jobs.pop(request_id, None)
            changed = True
            if hasattr(st, "toast"):
                error = data.get("error") or "GENERATION_JOB_FAILED"
                st.toast(f"이미지 생성에 실패했어요: {error}")

    if changed:
        st.session_state[ACTIVE_GENERATION_JOBS_KEY] = jobs
