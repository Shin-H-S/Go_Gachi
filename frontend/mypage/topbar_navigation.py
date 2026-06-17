import streamlit as st

from frontend.core.router import navigate_to
from frontend.home_button import (
    HOME_BUTTON_HELP,
    HOME_BUTTON_LABEL,
    WORK_BUTTON_HELP,
    WORK_BUTTON_LABEL,
)

__all__ = [
    "HOME_BUTTON_HELP",
    "HOME_BUTTON_LABEL",
    "WORK_BUTTON_HELP",
    "WORK_BUTTON_LABEL",
    "render_navigation_buttons",
]


def _render_home_button() -> None:
    with st.container(key="mypage-main-link-control"):
        if st.button(HOME_BUTTON_LABEL, key="mypage-main-link", help=HOME_BUTTON_HELP):
            navigate_to("main")
            st.rerun()


def _render_work_button() -> None:
    with st.container(key="mypage-work-link-control"):
        if st.button(WORK_BUTTON_LABEL, key="mypage-work-link", help=WORK_BUTTON_HELP):
            navigate_to("work")
            st.rerun()


def render_navigation_buttons() -> None:
    nav_cols = st.columns([1, 0.12, 0.12], gap="small")
    with nav_cols[1]:
        _render_work_button()
    with nav_cols[2]:
        _render_home_button()
