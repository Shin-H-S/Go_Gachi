from html import escape

import streamlit as st

from frontend.auth.session import clear_auth_session
from frontend.core.router import navigate_to
from frontend.mypage.components import render_generation_grid
from frontend.mypage.state import filter_generations, format_date, profile_name
from frontend.services.api_client import data_url_to_bytes


def render_recent_work(generations: list[dict], folders: list[dict], access_token: str) -> None:
    render_generation_grid(generations, folders, access_token)


def render_folder_view(
    view: str,
    generations: list[dict],
    folders: list[dict],
    access_token: str,
) -> None:
    render_generation_grid(filter_generations(generations, view), folders, access_token)


def render_uploads(uploads: list[dict]) -> None:
    if not uploads:
        st.markdown(
            """
            <div class="mypage-empty-state">
                <strong>업로드한 메뉴 사진이 없습니다</strong>
                <span>작업 페이지에서 메뉴 사진을 올리면 여기에 모입니다.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    columns = st.columns(4, gap="medium")
    for index, item in enumerate(uploads):
        image_data_url = str(item.get("image_data_url") or "")
        with columns[index % 4]:
            with st.container(border=True):
                if image_data_url:
                    st.image(data_url_to_bytes(image_data_url), use_container_width=True)
                else:
                    st.markdown(
                        '<div class="mypage-empty-thumb">이미지 없음</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f"""
                    <div class="mypage-card-meta">
                        <span>원본 사진</span>
                        <span>{int(item.get("used_count") or 0)}회 사용</span>
                    </div>
                    <div class="mypage-card-date">
                        {escape(format_date(item.get("created_at")))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_account_settings(profile: dict) -> None:
    display_name = profile_name(profile)
    st.markdown(
        f"""
        <div class="mypage-account-panel">
            <div>
                <span>닉네임</span>
                <strong>{escape(display_name)}</strong>
            </div>
            <div>
                <span>이메일</span>
                <strong>{escape(str(profile.get("email") or "-"))}</strong>
            </div>
            <div>
                <span>권한</span>
                <strong>{escape(str(profile.get("role") or "user"))}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("로그아웃", key="mypage-logout", use_container_width=False):
        clear_auth_session(st.session_state, "로그아웃되었습니다.")
        navigate_to("main")
        st.rerun()
