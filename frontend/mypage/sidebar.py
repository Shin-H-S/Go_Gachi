from functools import cache
from html import escape
from pathlib import Path

import httpx
import streamlit as st

from frontend.media.image_data import bytes_to_data_url
from frontend.mypage.folder_management import render_folder_row
from frontend.mypage.state import (
    ACCOUNT_VIEW,
    FOLDER_NONE_VIEW,
    RECENT_VIEW,
    UPLOADS_VIEW,
    profile_name,
    set_view,
)
from frontend.services.api_client import create_my_folder

MYPAGE_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"


@cache
def _sidebar_asset_data_url(filename: str) -> str:
    return bytes_to_data_url((MYPAGE_ASSET_DIR / filename).read_bytes())


def _sidebar_button_marker() -> None:
    st.markdown(
        '<span class="mypage-sidebar-button-marker" aria-hidden="true"></span>',
        unsafe_allow_html=True,
    )


def _render_sidebar_icon_visual(filename: str, css_class: str) -> None:
    asset_src = escape(_sidebar_asset_data_url(filename), quote=True)
    st.markdown(
        f"""
        <span class="mypage-icon-button-visual {css_class}" aria-hidden="true">
            <img src="{asset_src}" alt="" />
        </span>
        """,
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
    with st.container(key="mypage-settings-control"):
        _render_sidebar_icon_visual("gear.png", "mypage-settings-icon")
        if st.button(" ", key="mypage-settings", help="계정 설정"):
            set_view(ACCOUNT_VIEW)
            st.rerun()
    st.markdown('<div class="mypage-nav-label">내 자료</div>', unsafe_allow_html=True)
    _sidebar_button_marker()
    if st.button("전체 작업", key="mypage-nav-recent", use_container_width=True):
        set_view(RECENT_VIEW)
        st.rerun()
    _sidebar_button_marker()
    if st.button("업로드한 원본 이미지", key="mypage-nav-uploads", use_container_width=True):
        set_view(UPLOADS_VIEW)
        st.rerun()
    st.markdown('<div class="mypage-nav-label">폴더</div>', unsafe_allow_html=True)
    _sidebar_button_marker()
    if st.button("미분류", key="mypage-folder-none", use_container_width=True):
        set_view(FOLDER_NONE_VIEW)
        st.rerun()
    for folder in folders:
        render_folder_row(
            folder,
            view=view,
            access_token=access_token,
            sidebar_button_marker=_sidebar_button_marker,
        )
    with st.container(key="mypage-new-folder-control"):
        _render_sidebar_icon_visual("new-folder.png", "mypage-new-folder-icon")
        if st.button(" ", key="mypage-new-folder", help="새 폴더 만들기"):
            st.session_state["mypage_show_folder_form"] = not st.session_state.get(
                "mypage_show_folder_form",
                False,
            )
    if st.session_state.get("mypage_show_folder_form"):
        _render_folder_form(access_token)
