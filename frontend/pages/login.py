import streamlit as st

from frontend.auth.session import (
    AuthConfigurationError,
    AuthLoginError,
    login_with_email,
    save_auth_session,
)
from frontend.core.router import navigate_to


def _hide_streamlit_chrome() -> None:
    st.markdown(
        """
        <style>
            .main .block-container,
            [data-testid="stMainBlockContainer"] {
                max-width: none !important;
                padding: 0 !important;
            }

            [data-testid="stHeader"],
            [data-testid="stToolbar"],
            [data-testid="stDecoration"],
            #MainMenu,
            footer {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _handle_login_submit() -> str:
    email = st.session_state.get("login_email", "").strip()
    password = st.session_state.get("login_password", "")

    if not email or not password:
        return "이메일과 비밀번호를 모두 입력해주세요."

    try:
        auth_session = login_with_email(email, password)
    except (AuthConfigurationError, AuthLoginError) as exc:
        return str(exc)

    save_auth_session(st.session_state, auth_session)
    redirect_page = st.session_state.get("auth_redirect_page") or "work"
    st.session_state["auth_redirect_page"] = ""
    navigate_to(redirect_page)
    st.rerun()
    return ""


def render_login_page() -> None:
    _hide_streamlit_chrome()
    form_error = ""

    with st.container(key="login-page"):
        left_col, right_col = st.columns([1, 1], gap="small")

        with left_col:
            st.markdown(
                """
                <a class="login-brand" href="?page=main" target="_self">
                    Go Gachi<span>*</span>
                </a>
                <section class="login-heading" aria-label="로그인 안내">
                    <h1>다시 만나 반가워요</h1>
                    <p>이메일과 비밀번호로 로그인하세요</p>
                </section>
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.get("auth_notice"):
                st.info(st.session_state["auth_notice"])
            elif st.session_state.get("auth_error"):
                st.info("다시 로그인해주세요.")

            with st.form("email-login-form", clear_on_submit=False):
                st.markdown('<div class="login-form-fields-marker"></div>', unsafe_allow_html=True)
                st.text_input(
                    "이메일",
                    placeholder="이메일을 입력하세요",
                    key="login_email",
                )
                st.text_input(
                    "비밀번호",
                    placeholder="비밀번호를 입력하세요",
                    type="password",
                    key="login_password",
                )
                submitted = st.form_submit_button(
                    "로그인",
                    use_container_width=True,
                    type="primary",
                )

            if submitted:
                form_error = _handle_login_submit()

            if form_error:
                st.error(form_error)

            st.markdown(
                """
                <div class="login-links">
                    <a href="?page=main" target="_self">비밀번호를 잊으셨나요?</a>
                    <p>
                        아직 계정이 없으신가요?
                        <a href="?page=signup" target="_self">회원가입</a>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with right_col:
            st.markdown(
                '<div class="login-blue-panel" aria-hidden="true"></div>',
                unsafe_allow_html=True,
            )
