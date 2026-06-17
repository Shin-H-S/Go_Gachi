import streamlit as st

from frontend.auth.session import clear_auth_session
from frontend.core.router import navigate_to


def is_main_user_logged_in() -> bool:
    return bool(st.session_state.get("auth_access_token"))


def handle_logout_click() -> None:
    clear_auth_session(st.session_state, "濡쒓렇?꾩썐?섏뿀?듬땲??")
    navigate_to("main")
    st.rerun()


def render_main_navigation() -> None:
    if is_main_user_logged_in():
        st.markdown(
            """
            <nav class="landing-nav" aria-label="Go Gachi navigation">
                <div class="landing-brand">Go Gachi<span>*</span></div>
                <div class="landing-auth landing-auth-logout-slot" aria-hidden="true"></div>
            </nav>
            """,
            unsafe_allow_html=True,
        )
        if st.button("濡쒓렇?꾩썐", key="main-logout-button"):
            handle_logout_click()
        return

    st.markdown(
        """
        <nav class="landing-nav" aria-label="Go Gachi navigation">
            <div class="landing-brand">Go Gachi<span>*</span></div>
            <div class="landing-auth">
                <a class="landing-login" href="?page=login" target="_self">濡쒓렇??/a>
                <a class="landing-signup" href="?page=signup" target="_self">?뚯썝媛??/a>
            </div>
        </nav>
        """,
        unsafe_allow_html=True,
    )
