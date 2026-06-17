from html import escape

import streamlit as st

from frontend.auth.session import clear_auth_session
from frontend.core.router import navigate_to
from frontend.mypage.state import profile_name


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
