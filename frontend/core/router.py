import streamlit as st

from frontend.core.config import FORMAT_OPTIONS

DEFAULT_PAGE = "main"
VALID_PAGE_NAMES = {"login", "main", "signup", "work"}


def normalize_page_name(page_name: str | list[str] | None) -> str:
    if isinstance(page_name, list):
        page_name = page_name[0] if page_name else None
    return page_name if page_name in VALID_PAGE_NAMES else DEFAULT_PAGE


def init_session_state() -> None:
    default_channel = next(iter(FORMAT_OPTIONS))
    if st.session_state.get("selected_channel") not in FORMAT_OPTIONS:
        st.session_state["selected_channel"] = default_channel

    auth_defaults = {
        "is_logged_in": False,
        "auth_access_token": "",
        "auth_user_id": "",
        "auth_user_email": "",
        "auth_error": "",
        "auth_notice": "",
    }
    for key, default_value in auth_defaults.items():
        st.session_state.setdefault(key, default_value)


def get_current_page() -> str:
    return normalize_page_name(st.query_params.get("page", DEFAULT_PAGE))


def navigate_to(page_name: str) -> None:
    st.query_params["page"] = normalize_page_name(page_name)

