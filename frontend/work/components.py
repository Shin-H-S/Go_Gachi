from html import escape

import streamlit as st

from frontend.core.config import CHANNEL_SLUGS, FORMAT_OPTIONS, get_existing_channel_asset_path
from frontend.core.router import navigate_to
from frontend.css.work_generation_lock import WORK_GENERATION_LOCK_CSS
from frontend.media.image_data import bytes_to_data_url
from frontend.services.api_client import request_asset_bytes, request_me

WORK_HEADER_PROFILE_KEY = "work_header_profile"
WORK_HEADER_PROFILE_TOKEN_KEY = "work_header_profile_token"


def render_channel_tabs(selected_label: str) -> None:
    st.markdown('<div class="channel-button-marker"></div>', unsafe_allow_html=True)
    labels = list(FORMAT_OPTIONS)
    columns = st.columns(len(labels), gap="small")

    for column, label in zip(columns, labels, strict=True):
        with column:
            asset_path = get_existing_channel_asset_path(label)
            selected_class = " is-active" if label == selected_label else ""
            if asset_path:
                channel_asset_src = bytes_to_data_url(asset_path.read_bytes())
                media_content = f'<img src="{channel_asset_src}" alt="{escape(label)} logo" />'
            else:
                media_content = f'<span class="channel-card-placeholder">{escape(label)}</span>'
            st.markdown(
                f"""
                <div class="channel-card-media{selected_class}">
                    {media_content}
                </div>
                """,
                unsafe_allow_html=True,
            )
            clicked = st.button(
                label,
                key=f"channel_{CHANNEL_SLUGS[label]}",
                type="primary" if label == selected_label else "secondary",
                use_container_width=True,
            )
            if clicked and label != selected_label:
                st.session_state["selected_channel"] = label
                st.rerun()


def _build_mypage_profile_summary(profile: dict, is_logged_in: bool) -> dict[str, str]:
    if not is_logged_in:
        return {"avatar": "?", "title": "마이페이지", "email": ""}

    display_name = str(profile.get("display_name") or "").strip()
    email = str(profile.get("email") or "").strip()
    fallback_name = email.split("@", 1)[0] if email and "@" in email else ""
    title_name = display_name or fallback_name
    avatar_source = display_name or fallback_name

    return {
        "avatar": (avatar_source[:1].upper() if avatar_source else "?"),
        "title": f"{title_name}의 마이페이지" if title_name else "마이페이지",
        "email": email,
    }


def _get_work_header_profile() -> dict:
    access_token = str(st.session_state.get("auth_access_token") or "")
    session_email = str(st.session_state.get("auth_user_email") or "")
    if not access_token:
        return {}

    cached_token = st.session_state.get(WORK_HEADER_PROFILE_TOKEN_KEY)
    cached_profile = st.session_state.get(WORK_HEADER_PROFILE_KEY)
    if cached_token == access_token and isinstance(cached_profile, dict):
        profile = dict(cached_profile)
    else:
        try:
            profile = dict(request_me(access_token))
        except Exception:
            profile = {}
        st.session_state[WORK_HEADER_PROFILE_TOKEN_KEY] = access_token
        st.session_state[WORK_HEADER_PROFILE_KEY] = profile

    if session_email and not profile.get("email"):
        profile["email"] = session_email
    return profile


def _render_mypage_profile_button() -> None:
    is_logged_in = bool(st.session_state.get("auth_access_token"))
    summary = _build_mypage_profile_summary(_get_work_header_profile(), is_logged_in)
    email_html = (
        f'<small>{escape(summary["email"])}</small>'
        if summary["email"]
        else ""
    )
    profile_html = (
        '<div class="work-profile-card" aria-hidden="true">'
        f'<div class="work-profile-avatar">{escape(summary["avatar"])}</div>'
        '<div class="work-profile-text">'
        f'<strong>{escape(summary["title"])}</strong>'
        f"{email_html}"
        "</div>"
        "</div>"
    )
    st.markdown(profile_html, unsafe_allow_html=True)
    if st.button(summary["title"], key="work-mypage-link", use_container_width=True):
        navigate_to("mypage")
        st.rerun()


def _render_header_download_button() -> None:
    result_url = st.session_state.get("result_image_url")
    result_bytes = st.session_state.get("result_bytes")
    if isinstance(result_bytes, bytes):
        st.download_button(
            "⇩ 다운로드",
            data=result_bytes,
            file_name="cafe_ad_maker_result.png",
            mime="image/png",
            key="work-header-download-button",
            use_container_width=True,
        )
        return

    if isinstance(result_url, str) and result_url:
        if st.button(
            "⇩ 다운로드",
            key="work-header-download-fetch",
            use_container_width=True,
        ):
            try:
                st.session_state["result_bytes"] = request_asset_bytes(result_url)
                st.rerun()
            except Exception as exc:
                st.error(f"결과 이미지를 다운로드할 수 없습니다: {exc}")
        return

    st.button(
        "⇩ 다운로드",
        key="work-header-download-empty",
        use_container_width=True,
        disabled=True,
    )


def render_header() -> None:
    button_col, _, download_col = st.container(key="work-hero").columns(
        [0.22, 0.60, 0.18],
        vertical_alignment="top",
    )
    with button_col:
        _render_mypage_profile_button()
    with download_col:
        _render_header_download_button()


def render_generation_lock_css() -> None:
    st.markdown(f"<style>\n{WORK_GENERATION_LOCK_CSS}\n</style>", unsafe_allow_html=True)
