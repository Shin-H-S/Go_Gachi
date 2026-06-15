from html import escape

import httpx
import streamlit as st

from frontend.mypage.state import (
    ACCOUNT_VIEW,
    FOLDER_NONE_VIEW,
    RECENT_VIEW,
    UPLOADS_VIEW,
    folder_view,
    profile_name,
    set_view,
)
from frontend.services.api_client import create_my_folder


def _sidebar_button_marker() -> None:
    st.markdown(
        '<span class="mypage-sidebar-button-marker" aria-hidden="true"></span>',
        unsafe_allow_html=True,
    )


def _render_folder_form(access_token: str) -> None:
    with st.form("mypage-folder-form", clear_on_submit=True):
        folder_name = st.text_input("새 폴더 이름", placeholder="예: 봄 신메뉴")
        _sidebar_button_marker()
        submit = st.form_submit_button("폴더 만들기", use_container_width=True)
        if submit:
            try:
                create_my_folder(access_token, folder_name)
            except httpx.HTTPStatusError as exc:
                detail = exc.response.json().get("detail", "폴더를 만들지 못했습니다.")
                st.error(detail)
            else:
                st.session_state["mypage_show_folder_form"] = False
                st.rerun()


def render_sidebar(profile: dict, folders: list[dict], view: str, access_token: str) -> None:
    display_name = profile_name(profile)
    sidebar_title = f"{display_name}의 마이페이지" if display_name else "닉네임의 마이페이지"
    st.markdown(
        f"""
        <div class="mypage-sidebar-head">
            <div class="mypage-avatar">{escape(display_name[:1]).upper() or "G"}</div>
            <div>
                <strong>{escape(sidebar_title)}</strong>
                <small>{escape(str(profile.get("email") or ""))}</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _sidebar_button_marker()
    if st.button("전체 작업", key="mypage-nav-recent", use_container_width=True):
        set_view(RECENT_VIEW)
        st.rerun()
    st.markdown('<div class="mypage-nav-label">폴더</div>', unsafe_allow_html=True)
    _sidebar_button_marker()
    if st.button("미분류", key="mypage-folder-none", use_container_width=True):
        set_view(FOLDER_NONE_VIEW)
        st.rerun()
    for folder in folders:
        folder_id = int(folder["id"])
        _sidebar_button_marker()
        if st.button(
            str(folder["name"]),
            key=f"mypage-folder-{folder_id}",
            use_container_width=True,
        ):
            set_view(folder_view(folder_id))
            st.rerun()
    st.markdown('<div class="mypage-nav-label">내 자료</div>', unsafe_allow_html=True)
    _sidebar_button_marker()
    if st.button("업로드한 원본 이미지", key="mypage-nav-uploads", use_container_width=True):
        set_view(UPLOADS_VIEW)
        st.rerun()
    _sidebar_button_marker()
    if st.button("계정 설정", key="mypage-nav-account", use_container_width=True):
        set_view(ACCOUNT_VIEW)
        st.rerun()
    _sidebar_button_marker()
    if st.button("새 폴더 만들기", key="mypage-new-folder", use_container_width=True):
        st.session_state["mypage_show_folder_form"] = not st.session_state.get(
            "mypage_show_folder_form",
            False,
        )
    if st.session_state.get("mypage_show_folder_form"):
        _render_folder_form(access_token)
