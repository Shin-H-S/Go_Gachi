import streamlit as st
from pages.main import render_main_page
from pages.work import render_work_page
from router import get_current_page, init_session_state
from styles import add_css

st.set_page_config(
    page_title="Go Gachi",
    page_icon="GG",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    init_session_state()
    add_css()

    if get_current_page() == "main":
        render_main_page()
        st.stop()

    render_work_page()


main()
