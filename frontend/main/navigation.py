import streamlit as st

from frontend.auth.session import clear_auth_session
from frontend.core.router import navigate_to

LOGIN_LABEL = "\ub85c\uadf8\uc778"
LOGOUT_LABEL = "\ub85c\uadf8\uc544\uc6c3"
LOGOUT_NOTICE = "\ub85c\uadf8\uc544\uc6c3\ub418\uc5c8\uc2b5\ub2c8\ub2e4."
SIGNUP_LABEL = "\ud68c\uc6d0\uac00\uc785"


def is_main_user_logged_in() -> bool:
    return bool(st.session_state.get("auth_access_token"))


def handle_logout_click() -> None:
    clear_auth_session(st.session_state, LOGOUT_NOTICE)
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
        if st.button(LOGOUT_LABEL, key="main-logout-button"):
            handle_logout_click()
        return

    st.markdown(
        f"""
        <nav class="landing-nav" aria-label="Go Gachi navigation">
            <div class="landing-brand">Go Gachi<span>*</span></div>
            <div class="landing-auth">
                <a class="landing-login" href="?page=login" target="_self">{LOGIN_LABEL}</a>
                <a class="landing-signup" href="?page=signup" target="_self">{SIGNUP_LABEL}</a>
            </div>
        </nav>
        """,
        unsafe_allow_html=True,
    )
