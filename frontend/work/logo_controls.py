from html import escape

import streamlit as st

from frontend.media.image_data import bytes_to_data_url
from frontend.work.logo_positions import (
    DEFAULT_LOGO_POSITION,
    LOGO_POSITION_LABELS,
    LOGO_POSITION_OPTIONS,
)
from frontend.work.uploads import UPLOAD_FILE_TYPES


def render_logo_preview(logo_file) -> None:
    if logo_file is None:
        preview_html = '<span class="logo-preview-placeholder">로고 이미지</span>'
    else:
        mime_type = getattr(logo_file, "type", None) or "image/png"
        logo_src = escape(bytes_to_data_url(logo_file.getvalue(), mime_type), quote=True)
        preview_html = f'<img src="{logo_src}" alt="로고 이미지" />'

    st.markdown(
        f'<div class="logo-preview-frame">{preview_html}</div>',
        unsafe_allow_html=True,
    )


def render_logo_controls():
    st.markdown('<p class="section-label">로고 업로드</p>', unsafe_allow_html=True)
    logo_file = st.file_uploader(
        "로고 이미지 업로드",
        type=UPLOAD_FILE_TYPES,
        accept_multiple_files=False,
        key="logo_upload",
        label_visibility="collapsed",
    )

    logo_position = st.selectbox(
        "로고 위치",
        options=LOGO_POSITION_OPTIONS,
        index=LOGO_POSITION_OPTIONS.index(DEFAULT_LOGO_POSITION),
        format_func=lambda value: LOGO_POSITION_LABELS[value],
        key="logo_position",
    )
    return logo_file, logo_position
