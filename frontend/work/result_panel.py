import streamlit as st

from frontend.work.preview import render_image_preview, render_preview_shell
from frontend.work.result_copy import render_result_copy
from frontend.work.result_summary import render_result_summary


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
    elif uploaded_file and "result_bytes" not in st.session_state:
        render_image_preview(uploaded_file.getvalue(), format_label, detail_label)
    elif "result_bytes" in st.session_state:
        render_image_preview(st.session_state["result_bytes"], format_label, detail_label)
        render_result_summary(st.session_state.get("result_context"))
        render_result_copy(st.session_state.get("result_copy"))
        st.download_button(
            "이미지 다운로드",
            data=st.session_state["result_bytes"],
            file_name="cafe_ad_maker_result.png",
            mime="image/png",
            use_container_width=True,
        )
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
