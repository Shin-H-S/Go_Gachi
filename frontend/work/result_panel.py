from functools import cache
from pathlib import Path

import streamlit as st

from frontend.media.image_data import bytes_to_data_url
from frontend.work.preview import (
    render_image_preview,
    render_image_url_preview,
    render_preview_shell,
)
from frontend.work.result_copy import result_copy_html
from frontend.work.result_summary import result_summary_html
from frontend.work.state import get_result_cursor, get_result_history, move_result_cursor

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


def _render_preview_history_controls(
    *,
    copy_html: str = "",
    cursor: int | None = None,
    total: int | None = None,
) -> None:
    if total is None:
        total = len(get_result_history())
    if cursor is None:
        cursor = get_result_cursor()

    _render_preview_history_css()
    # Mirror the generate button's marker so the arrow row lands at the same
    # height as the left "이미지 만들기" button.
    st.markdown('<div class="preview-controls-marker"></div>', unsafe_allow_html=True)
    with st.container(key="preview-history-controls"):
        undo_col, redo_col, copy_col, _spacer = st.columns(
            [0.12, 0.12, 0.36, 0.40], gap="small", vertical_alignment="top"
        )
        with undo_col:
            undo_clicked = st.button(
                " ",
                key="work-preview-undo",
                help="이전",
                use_container_width=True,
                disabled=cursor <= 0,
            )
        with redo_col:
            redo_clicked = st.button(
                " ",
                key="work-preview-redo",
                help="다음",
                use_container_width=True,
                disabled=cursor >= total,
            )
        with copy_col:
            if copy_html:
                st.markdown(copy_html, unsafe_allow_html=True)
    if undo_clicked:
        move_result_cursor(-1)
        st.rerun()
    if redo_clicked:
        move_result_cursor(1)
        st.rerun()


def render_result_panel(
    *,
    is_generating: bool,
    uploaded_file,
    format_label: str,
    detail_label: str,
) -> None:
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
        return

    history = get_result_history()
    total = len(history)
    cursor = get_result_cursor()
    result_context = st.session_state.get("result_context")
    result_copy = st.session_state.get("result_copy")
    result_url = st.session_state.get("result_image_url")
    result_bytes = st.session_state.get("result_bytes")

    if cursor >= 1 and total >= 1:
        entry = history[cursor - 1]
        entry_format = str(entry.get("format_label") or format_label)
        entry_detail = str(entry.get("detail_label") or detail_label)
        entry_context = entry.get("context")
        summary_html = result_summary_html(entry_context)
        entry_url = entry.get("url")
        entry_bytes = entry.get("bytes")
        if entry_url:
            render_image_url_preview(
                str(entry_url), entry_format, entry_detail, summary_html=summary_html
            )
        elif isinstance(entry_bytes, bytes):
            render_image_preview(entry_bytes, entry_format, entry_detail, summary_html=summary_html)
        else:
            render_preview_shell(entry_format, "", entry_detail)
        copy_html = result_copy_html(entry.get("copy"), result_context=entry_context)
        _render_preview_history_controls(copy_html=copy_html)
    elif result_url or isinstance(result_bytes, bytes):
        summary_html = result_summary_html(result_context)
        if result_url:
            render_image_url_preview(
                str(result_url), format_label, detail_label, summary_html=summary_html
            )
        else:
            render_image_preview(
                result_bytes, format_label, detail_label, summary_html=summary_html
            )
        copy_html = result_copy_html(result_copy, result_context=result_context)
        _render_preview_history_controls(copy_html=copy_html)
    elif uploaded_file:
        render_image_preview(uploaded_file.getvalue(), format_label, detail_label)
        _render_preview_history_controls()
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
