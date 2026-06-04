import streamlit as st

from frontend.auth.session import (
    AuthConfigurationError,
    AuthSignupError,
    signup_with_email,
)
from frontend.core.router import navigate_to
from frontend.pages.login import _hide_streamlit_chrome


def _handle_signup_submit() -> str:
    email = st.session_state.get("signup_email", "").strip()
    password = st.session_state.get("signup_password", "")
    display_name = st.session_state.get("signup_display_name", "").strip()

    try:
        signup_with_email(email, password, display_name)
    except (AuthConfigurationError, AuthSignupError) as exc:
        return str(exc)

    st.session_state["auth_notice"] = (
        "회원가입이 완료되었습니다. 이메일 인증을 마친 뒤 로그인해주세요."
    )
    navigate_to("login")
    st.rerun()
    return ""


def render_signup_page() -> None:
    _hide_streamlit_chrome()
    form_error = ""

    with st.container(key="signup-page"):
        left_col, right_col = st.columns([1, 1], gap="small")

        with left_col:
            st.markdown(
                """
                <a class="signup-brand" href="?page=main" target="_self">
                    Go Gachi<span>*</span>
                </a>
                <section class="signup-heading" aria-label="회원가입 안내">
                    <h1>회원가입</h1>
                    <p>광고 이미지를 만들 계정을 생성하세요</p>
                </section>
                """,
                unsafe_allow_html=True,
            )

            with st.form("email-signup-form", clear_on_submit=False):
                st.markdown('<div class="signup-form-fields-marker"></div>', unsafe_allow_html=True)
                st.text_input(
                    "이메일",
                    placeholder="이메일을 입력하세요",
                    key="signup_email",
                )
                st.text_input(
                    "닉네임",
                    placeholder="닉네임을 입력하세요",
                    key="signup_display_name",
                )
                st.text_input(
                    "비밀번호",
                    placeholder="8자 이상 입력하세요",
                    type="password",
                    key="signup_password",
                )
                submitted = st.form_submit_button(
                    "계정 만들기",
                    use_container_width=True,
                    type="primary",
                )

            if submitted:
                form_error = _handle_signup_submit()

            if form_error:
                st.error(form_error)

            st.markdown(
                """
                <div class="signup-links">
                    <p>이미 계정이 있으신가요? <a href="?page=login" target="_self">로그인</a></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right_col:
            st.markdown(
                '<div class="signup-blue-panel" aria-hidden="true"></div>',
                unsafe_allow_html=True,
            )
