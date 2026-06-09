import streamlit as st

from frontend.work.copy import build_auto_copy, copy_mode_for_prompt


def _fill_auto_copy(format_label: str, detail_label: str) -> None:
    st.session_state["ad_copy_prompt"] = build_auto_copy(format_label, detail_label)


def render_copy_controls(format_label: str, detail_label: str) -> tuple[str, bool, str]:
    st.markdown('<p class="section-label">광고 문구</p>', unsafe_allow_html=True)
    text_overlay_enabled = st.checkbox(
        "광고 문구 포함",
        value=True,
        key="text_overlay_enabled",
    )
    raw_prompt = st.text_area(
        "광고 문구",
        placeholder=(
            "직접 넣고 싶은 광고 문구를 입력하세요.\n"
            "비워두면 자동 문구 생성을 요청합니다."
        ),
        height=150,
        disabled=not text_overlay_enabled,
        key="ad_copy_prompt",
        help="비워두면 이미지 생성 시 자동 문구 생성을 요청합니다.",
        label_visibility="collapsed",
    )
    if text_overlay_enabled:
        st.button(
            "광고 문구 자동 생성",
            key="auto_copy_generate",
            on_click=_fill_auto_copy,
            args=(format_label, detail_label),
            use_container_width=True,
        )

    prompt = raw_prompt if text_overlay_enabled else ""
    copy_mode = copy_mode_for_prompt(
        text_overlay_enabled=text_overlay_enabled,
        prompt=prompt,
    )
    return prompt, text_overlay_enabled, copy_mode

