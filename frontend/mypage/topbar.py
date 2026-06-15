from html import escape

import streamlit as st

from frontend.core.router import navigate_to
from frontend.mypage.state import FOLDER_PREFIX


def render_topbar(view: str, title: str, access_token: str) -> None:  # noqa: ARG001
    title_col, action_col = st.columns([0.64, 0.36], gap="large")
    with title_col:
        st.markdown(f'<h1 class="mypage-title">{escape(title)}</h1>', unsafe_allow_html=True)
    with action_col:
        if view.startswith(FOLDER_PREFIX):
            if st.button(
                "← 작업 페이지로 돌아가기",
                key="mypage-new-work",
                use_container_width=True,
            ):
                navigate_to("work")
                st.rerun()
        elif st.button(
            "← 작업 페이지로 돌아가기",
            key="mypage-new-work-simple",
            use_container_width=True,
        ):
            navigate_to("work")
            st.rerun()
