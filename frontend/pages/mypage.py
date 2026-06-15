import time

import httpx
import streamlit as st

from frontend.core.router import navigate_to
from frontend.mypage import views
from frontend.mypage.components import render_sidebar, render_topbar
from frontend.mypage.generation_status import has_generation_waiting_for_image
from frontend.mypage.page_sections import (
    render_account_settings,
    render_folder_view,
    render_recent_work,
    render_uploads,
)
from frontend.mypage.pagination import page_count
from frontend.mypage.state import (
    ACCOUNT_VIEW,
    FOLDER_ALL_VIEW,
    RECENT_VIEW,
    UPLOADS_VIEW,
    view_title,
)
from frontend.services.api_client import (
    request_me,
    request_my_folders,
    request_my_generations,
    request_my_uploads,
)

BACKEND_GENERATION_PAGE_SIZE = 10
PENDING_REFRESH_SESSION_KEY = "mypage_pending_refresh_last_at"
PENDING_REFRESH_INTERVAL_SECONDS = 3.0

MYPAGE_COPY_MARKERS = (
    "닉네임의 마이페이지", "전체 작업", "업로드한 원본 이미지",
    "계정 설정", "새 폴더 만들기", "작업 페이지로 돌아가기",
)


@st.fragment(run_every="3s")
def _pending_generation_auto_refresh() -> None:
    now = time.monotonic()
    last_refresh = st.session_state.get(PENDING_REFRESH_SESSION_KEY)
    if last_refresh is None:
        st.session_state[PENDING_REFRESH_SESSION_KEY] = now
        return
    try:
        elapsed = now - float(last_refresh)
    except (TypeError, ValueError):
        elapsed = PENDING_REFRESH_INTERVAL_SECONDS
    if elapsed >= PENDING_REFRESH_INTERVAL_SECONDS:
        st.session_state[PENDING_REFRESH_SESSION_KEY] = now
        st.rerun()


def _maybe_render_pending_generation_auto_refresh(generations: list[dict]) -> None:
    if has_generation_waiting_for_image(generations):
        _pending_generation_auto_refresh()
        return
    st.session_state.pop(PENDING_REFRESH_SESSION_KEY, None)


def _load_generation_pages(access_token: str) -> tuple[list[dict], int]:
    generations: list[dict] = []
    page = 1
    total_count = 0
    while True:
        payload = request_my_generations(access_token, page=page)
        items = list(payload.get("items", []))
        if page == 1:
            total_count = int(payload.get("total_count") or len(items))
        generations.extend(items)
        if not items or len(generations) >= total_count:
            return generations, total_count
        page += 1


def _safe_page(value: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return 1


def _load_recent_generation_slice(access_token: str, page: int) -> tuple[list[dict], int]:
    page = _safe_page(page)
    start = (page - 1) * views.GENERATION_PAGE_SIZE
    end = start + views.GENERATION_PAGE_SIZE
    first_backend_page = (start // BACKEND_GENERATION_PAGE_SIZE) + 1

    first_payload = request_my_generations(access_token, page=first_backend_page)
    first_items = list(first_payload.get("items", []))
    total_count = int(first_payload.get("total_count") or (start + len(first_items)))

    combined_items = first_items
    effective_end = min(end, total_count)
    last_backend_page = (
        ((effective_end - 1) // BACKEND_GENERATION_PAGE_SIZE) + 1
        if effective_end > start
        else first_backend_page
    )
    for backend_page in range(first_backend_page + 1, last_backend_page + 1):
        payload = request_my_generations(access_token, page=backend_page)
        combined_items.extend(list(payload.get("items", [])))

    first_backend_start = (first_backend_page - 1) * BACKEND_GENERATION_PAGE_SIZE
    offset = start - first_backend_start
    return combined_items[offset : offset + views.GENERATION_PAGE_SIZE], total_count


def _load_recent_generation_page(
    access_token: str,
    page: int,
) -> tuple[list[dict], int, int]:
    requested_page = _safe_page(page)
    generations, total_count = _load_recent_generation_slice(access_token, requested_page)
    current_page = min(requested_page, page_count(total_count, views.GENERATION_PAGE_SIZE))
    if current_page != requested_page:
        generations, total_count = _load_recent_generation_slice(access_token, current_page)
    return generations, total_count, current_page


def _load_mypage_data(
    access_token: str,
    view: str,
) -> tuple[dict, list[dict], list[dict], list[dict], int, int]:
    profile = request_me(access_token)
    folders = list(request_my_folders(access_token).get("items", []))
    generations: list[dict] = []
    uploads: list[dict] = []
    generation_total_count = 0
    generation_current_page = 1
    if view == RECENT_VIEW:
        generations, generation_total_count, generation_current_page = _load_recent_generation_page(
            access_token,
            views.current_page("recent"),
        )
    elif view == UPLOADS_VIEW:
        uploads = list(request_my_uploads(access_token).get("items", []))
    elif view != ACCOUNT_VIEW:
        generations, generation_total_count = _load_generation_pages(access_token)
    return profile, folders, generations, uploads, generation_total_count, generation_current_page


def _render_login_required() -> None:
    st.warning("로그인 후 마이페이지를 사용할 수 있습니다.")
    if st.button("로그인으로 이동", key="mypage-login-link"):
        st.session_state["auth_redirect_page"] = "mypage"
        navigate_to("login")
        st.rerun()


def render_mypage_page() -> None:
    access_token = st.session_state.get("auth_access_token", "")
    if not access_token:
        _render_login_required()
        return

    view = st.session_state.get("mypage_view", RECENT_VIEW)
    if view == FOLDER_ALL_VIEW:
        view = RECENT_VIEW
        st.session_state["mypage_view"] = RECENT_VIEW
    try:
        profile, folders, generations, uploads, generation_total_count, generation_current_page = (
            _load_mypage_data(access_token, view)
        )
    except httpx.HTTPError:
        st.error("마이페이지 정보를 불러오지 못했습니다. 다시 로그인해주세요.")
        return

    _maybe_render_pending_generation_auto_refresh(generations)

    title = view_title(view, folders)
    with st.container(key="mypage-shell"):
        left_col, right_col = st.columns([0.176, 0.824], gap="large")

        with left_col:
            render_sidebar(profile, folders, view, access_token)

        with right_col:
            render_topbar(view, title, access_token)
            if view == RECENT_VIEW:
                render_recent_work(
                    generations,
                    folders,
                    access_token,
                    total_count=generation_total_count,
                    current_page=generation_current_page,
                )
            elif view == UPLOADS_VIEW:
                render_uploads(uploads)
            elif view == ACCOUNT_VIEW:
                render_account_settings(profile)
            else:
                render_folder_view(view, generations, folders, access_token)
