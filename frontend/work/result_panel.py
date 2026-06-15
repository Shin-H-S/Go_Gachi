from functools import cache
from pathlib import Path

import streamlit as st

from frontend.media.image_data import bytes_to_data_url
from frontend.work.preview import (
    render_image_preview,
    render_image_url_preview,
    render_preview_shell,
)
from frontend.work.result_copy import render_result_copy
from frontend.work.result_summary import render_result_summary

_ARROW_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"


@cache
def _arrow_data_url(filename: str) -> str:
    return bytes_to_data_url((_ARROW_ASSET_DIR / filename).read_bytes())


def _render_preview_history_css() -> None:
    undo_src = _arrow_data_url("left-arrow.png")
    redo_src = _arrow_data_url("right-arrow.png")
    st.markdown(
        f"""
        <style>
        .st-key-work-preview-undo button,
        .st-key-work-preview-redo button {{
            position: relative !important;
        }}
        .st-key-work-preview-undo button::after,
        .st-key-work-preview-redo button::after {{
            content: "";
            position: absolute;
            inset: 0;
            background-repeat: no-repeat;
            background-position: center;
            background-size: auto 50%;
            pointer-events: none;
        }}
        .st-key-work-preview-undo button::after {{
            background-image: url("{undo_src}");
        }}
        .st-key-work-preview-redo button::after {{
            background-image: url("{redo_src}");
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_preview_history_controls() -> None:
    _render_preview_history_css()
    with st.container(key="preview-history-controls"):
        st.markdown('<div class="preview-history-controls"></div>', unsafe_allow_html=True)
        _, undo_col, redo_col, _ = st.columns([0.28, 0.22, 0.22, 0.28], gap="small")
        with undo_col:
            undo_clicked = st.button(
                " ",
                key="work-preview-undo",
                help="되돌리기",
                use_container_width=True,
            )
        with redo_col:
            redo_clicked = st.button(
                " ",
                key="work-preview-redo",
                help="다시 실행",
                use_container_width=True,
            )

    if undo_clicked:
        st.info("되돌릴 이전 결과가 아직 없습니다.")
    if redo_clicked:
        st.info("다시 실행할 다음 결과가 아직 없습니다.")


def render_result_panel(
    *,
    is_generating: bool,
    uploaded_file,
    format_label: str,
    detail_label: str,
) -> None:
    result_url = st.session_state.get("result_image_url")
    result_bytes = st.session_state.get("result_bytes")

    if is_generating:
        render_preview_shell(
            format_label,
            """
            <div class="loading-state">
                <div class="loading-panel">
                    <div class="loading-spinner"></div>
                    <div>제작 중입니다. 잠시만 기다려주세요.</div>
                </div>
            </div>
            """,
            detail_label,
        )
    elif uploaded_file and not result_url and result_bytes is None:
        render_image_preview(uploaded_file.getvalue(), format_label, detail_label)
        _render_preview_history_controls()
    elif result_url:
        render_image_url_preview(str(result_url), format_label, detail_label)
        _render_preview_history_controls()
        render_result_summary(st.session_state.get("result_context"))
        render_result_copy(st.session_state.get("result_copy"))
    elif isinstance(result_bytes, bytes):
        render_image_preview(result_bytes, format_label, detail_label)
        _render_preview_history_controls()
        render_result_summary(st.session_state.get("result_context"))
        render_result_copy(st.session_state.get("result_copy"))
    else:
        render_preview_shell(
            format_label,
            """
            <div class="empty-guide">
                단순한 배경에서, 광고에 사용할 각도로 촬영한 이미지를 올려주세요.
            </div>
            """,
            detail_label,
        )
        _render_preview_history_controls()
