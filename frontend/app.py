import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.core.router import get_current_page, init_session_state  # noqa: E402
from frontend.pages.login import render_login_page  # noqa: E402
from frontend.pages.main import render_main_page  # noqa: E402
from frontend.pages.signup import render_signup_page  # noqa: E402
from frontend.pages.work import render_work_page  # noqa: E402
from frontend.styles import add_css  # noqa: E402

st.set_page_config(
    page_title="Go Gachi",
    page_icon="GG",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    init_session_state()
    add_css()
    current_page = get_current_page()

    if current_page == "main":
        render_main_page()
        st.stop()

    if current_page == "login":
        render_login_page()
        st.stop()

    if current_page == "signup":
        render_signup_page()
        st.stop()

    render_work_page()


main()
