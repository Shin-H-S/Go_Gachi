from html import escape

import streamlit as st
from image_data import bytes_to_data_url

from config import CHANNEL_SLUGS, FORMAT_OPTIONS, get_existing_channel_asset_path


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
                media_content = (
                    f'<img src="{channel_asset_src}" alt="{escape(label)} logo" />'
                )
            else:
                media_content = (
                    f'<span class="channel-card-placeholder">{escape(label)}</span>'
                )
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


def render_header() -> None:
    st.markdown(
        """
        <div class="topbar">
            <p class="brand-kicker">GO-GACHI CAFE AD MAKER V1</p>
            <h1 class="title">카페 메뉴 광고 이미지 제작</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )





def render_generation_lock_css() -> None:
    st.markdown(
        """
<style>
    div[role="radiogroup"] label:not(:has(input:checked)) {
        opacity: 0.34;
        pointer-events: none;
    }

    div[role="radiogroup"] label:has(input:checked) {
        opacity: 1;
    }

    .channel-tab:not(.is-active),
    div[data-testid="stSegmentedControl"]
        button:not([aria-pressed="true"]):not([data-selected="true"]) {
        opacity: 0.34;
        pointer-events: none;
    }

    div[data-testid="stElementContainer"]:has(.channel-button-marker)
        + div[data-testid="stHorizontalBlock"]
        button[data-testid="stBaseButton-secondary"] {
        opacity: 0.34;
        pointer-events: none;
    }

    .channel-tab.is-active,
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"],
    div[data-testid="stSegmentedControl"] button[data-selected="true"] {
        opacity: 1;
    }

    div[data-testid="stElementContainer"]:has(.channel-button-marker)
        + div[data-testid="stHorizontalBlock"]
        button[data-testid="stBaseButton-primary"] {
        opacity: 1;
    }

    div[data-testid="stButton"] button[kind="primary"],
    div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] {
        background: #aab7b3 !important;
        color: #eef3f1 !important;
        -webkit-text-fill-color: #eef3f1 !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
        pointer-events: none;
    }

    div[data-testid="stButton"] button[kind="primary"] *,
    div[data-testid="stButton"] button[data-testid="stBaseButton-primary"] * {
        color: #eef3f1 !important;
        -webkit-text-fill-color: #eef3f1 !important;
    }
</style>
        """,
        unsafe_allow_html=True,
    )
