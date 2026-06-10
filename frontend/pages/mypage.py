import httpx
import streamlit as st

from frontend.core.router import navigate_to
from frontend.mypage import views
from frontend.mypage.components import render_sidebar, render_topbar
from frontend.mypage.state import ACCOUNT_VIEW, RECENT_VIEW, UPLOADS_VIEW, view_title
from frontend.services.api_client import (
    request_me,
    request_my_folders,
    request_my_generations,
    request_my_uploads,
)

MYPAGE_COPY_MARKERS = (
    "닉네임의 마이페이지",
    "업로드한 메뉴 사진",
    "계정 설정",
    "새 폴더 만들기",
    "새로 생성하기",
)


def render_recent_work(generations: list[dict], folders: list[dict], access_token: str) -> None:
    views.render_recent_work(generations, folders, access_token)


def render_folder_view(
    view: str,
    generations: list[dict],
    folders: list[dict],
    access_token: str,
) -> None:
    views.render_folder_view(view, generations, folders, access_token)


def render_uploads(uploads: list[dict]) -> None:
    views.render_uploads(uploads)


def render_account_settings(profile: dict) -> None:
    views.render_account_settings(profile)


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


def _load_mypage_data(access_token: str) -> tuple[dict, list[dict], list[dict], list[dict]]:
    profile = request_me(access_token)
    folders = list(request_my_folders(access_token).get("items", []))
    generations, total_count = _load_generation_pages(access_token)
    uploads = list(request_my_uploads(access_token).get("items", []))
    return profile, folders, generations, uploads


def _render_login_required() -> None:
    st.warning("로그인 후 마이페이지를 사용할 수 있습니다.")
    if st.button("로그인으로 이동", key="mypage-login-link"):
        navigate_to("login")
        st.rerun()


def render_mypage_page() -> None:
    access_token = st.session_state.get("auth_access_token", "")
    if not access_token:
        _render_login_required()
        return

    try:
        profile, folders, generations, uploads = _load_mypage_data(access_token)
    except httpx.HTTPError:
        st.error("마이페이지 정보를 불러오지 못했습니다. 다시 로그인해주세요.")
        return

    view = st.session_state.get("mypage_view", RECENT_VIEW)
    title = view_title(view, folders)
    with st.container(key="mypage-shell"):
        left_col, right_col = st.columns([0.22, 0.78], gap="large")

        with left_col:
            render_sidebar(profile, folders, view, access_token)

        with right_col:
            render_topbar(view, title, access_token)
            if view == RECENT_VIEW:
                render_recent_work(generations, folders, access_token)
            elif view == UPLOADS_VIEW:
                render_uploads(uploads)
            elif view == ACCOUNT_VIEW:
                render_account_settings(profile)
            else:
                render_folder_view(view, generations, folders, access_token)
