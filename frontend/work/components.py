from functools import cache
from html import escape
from pathlib import Path

import streamlit as st

from frontend.core.config import CHANNEL_SLUGS, FORMAT_OPTIONS, get_existing_channel_asset_path
from frontend.media.image_data import bytes_to_data_url
from frontend.work import header as _header

WORK_HEADER_PROFILE_KEY = _header.WORK_HEADER_PROFILE_KEY
WORK_HEADER_PROFILE_TOKEN_KEY = _header.WORK_HEADER_PROFILE_TOKEN_KEY
_build_mypage_profile_summary = _header._build_mypage_profile_summary
_get_work_header_profile = _header._get_work_header_profile
render_generation_lock_css = _header.render_generation_lock_css
render_header = _header.render_header

WORK_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"

__all__ = [
    "WORK_HEADER_PROFILE_KEY",
    "WORK_HEADER_PROFILE_TOKEN_KEY",
    "_build_mypage_profile_summary",
    "_get_work_header_profile",
    "render_channel_tabs",
    "render_generation_lock_css",
    "render_header",
    "render_section_label",
]


@cache
def _label_icon_data_url(filename: str) -> str:
    return bytes_to_data_url((WORK_ASSET_DIR / filename).read_bytes())


def render_section_label(
    text: str,
    icon_filename: str,
    css_class: str = "section-label",
) -> None:
    """Render a work-page section label with a leading icon sized to the text."""
    icon_src = escape(_label_icon_data_url(icon_filename), quote=True)
    st.markdown(
        f'<p class="{css_class}">'
        f'<img class="label-icon" src="{icon_src}" alt="" aria-hidden="true" /> '
        f"{escape(text)}</p>",
        unsafe_allow_html=True,
    )


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
