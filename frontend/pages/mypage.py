import time

import httpx
import streamlit as st

from frontend.core.router import navigate_to
from frontend.mypage import data_loader, views
from frontend.mypage.cache import (
    cached_request_me,
    cached_request_my_folders,
    cached_request_my_generations,
    cached_request_my_uploads,
    clear_generation_cache,
)
from frontend.mypage.components import render_sidebar, render_topbar
from frontend.mypage.generation_status import has_generation_waiting_for_image
from frontend.mypage.page_sections import (
    render_account_settings,
    render_folder_view,
    render_recent_work,
    render_uploads,
)
from frontend.mypage.state import (
    ACCOUNT_VIEW,
    FOLDER_ALL_VIEW,
    FOLDER_NONE_VIEW,
    RECENT_VIEW,
    UPLOADS_VIEW,
    selected_folder_id,
    view_title,
)

BACKEND_GENERATION_PAGE_SIZE = data_loader.BACKEND_GENERATION_PAGE_SIZE
PENDING_REFRESH_SESSION_KEY = "mypage_pending_refresh_last_at"
PENDING_REFRESH_INTERVAL_SECONDS = 5.0

MYPAGE_COPY_MARKERS = (
    "닉네임의 마이페이지",
    "전체 작업",
    "업로드한 원본 이미지",
    "계정 설정",
    "새 폴더 만들기",
    "작업 페이지로 돌아가기",
)


@st.fragment(run_every="5s")
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
        clear_generation_cache()
        st.rerun()


def _maybe_render_pending_generation_auto_refresh(generations: list[dict]) -> None:
    if has_generation_waiting_for_image(generations):
        _pending_generation_auto_refresh()
        return
    st.session_state.pop(PENDING_REFRESH_SESSION_KEY, None)


def _load_recent_generation_page(
    access_token: str,
    page: int,
    *,
    folder_id: int | None = None,
    uncategorized: bool = False,
) -> tuple[list[dict], int, int]:
    return data_loader.load_recent_generation_page(
        cached_request_my_generations,
        access_token,
        page,
        folder_id=folder_id,
        uncategorized=uncategorized,
    )


def _load_upload_page(
    access_token: str,
    page: int,
) -> tuple[list[dict], int, int]:
    return data_loader.load_upload_page(
        cached_request_my_uploads,
        access_token,
        page,
    )


def _load_mypage_data(
    access_token: str,
    view: str,
) -> tuple[dict, list[dict], list[dict], list[dict], int, int]:
    profile = cached_request_me(access_token)
    folders = list(cached_request_my_folders(access_token).get("items", []))
    generations: list[dict] = []
    uploads: list[dict] = []
    total_count = 0
    current_page = 1
    if view in (RECENT_VIEW, FOLDER_ALL_VIEW):
        scope = "recent" if view == RECENT_VIEW else view
        generations, total_count, current_page = _load_recent_generation_page(
            access_token,
            views.current_page(scope),
        )
    elif view == UPLOADS_VIEW:
        uploads, total_count, current_page = _load_upload_page(
            access_token,
            views.current_page("uploads"),
        )
    elif view != ACCOUNT_VIEW:
        folder_id = selected_folder_id(view)
        if folder_id is not None:
            generations, total_count, current_page = _load_recent_generation_page(
                access_token,
                views.current_page(view),
                folder_id=folder_id,
            )
        elif view == FOLDER_NONE_VIEW:
            generations, total_count, current_page = _load_recent_generation_page(
                access_token,
                views.current_page(view),
                uncategorized=True,
            )
    return profile, folders, generations, uploads, total_count, current_page


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
        profile, folders, generations, uploads, total_count, current_page = _load_mypage_data(
            access_token,
            view,
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
            render_topbar(view, title, access_token, generations=generations, folders=folders)
            if view == RECENT_VIEW:
                render_recent_work(
                    generations,
                    folders,
                    access_token,
                    total_count=total_count,
                    current_page=current_page,
                )
            elif view == UPLOADS_VIEW:
                render_uploads(
                    uploads,
                    total_count=total_count,
                    current_page=current_page,
                )
            elif view == ACCOUNT_VIEW:
                render_account_settings(profile)
            elif selected_folder_id(view) is not None:
                render_folder_view(
                    view,
                    generations,
                    folders,
                    access_token,
                    total_count=total_count,
                    current_page=current_page,
                )
            else:
                render_folder_view(view, generations, folders, access_token)
