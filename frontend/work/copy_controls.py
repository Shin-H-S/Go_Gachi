import streamlit as st

from frontend.work.copy import COPY_MODE_OPTIONS


def render_copy_controls(
    format_label: str,
    detail_label: str,
    image_prompt: str = "",
) -> tuple[str, bool, str]:
    ad_copy_enabled = st.checkbox(
        "광고 문구 포함",
        value=True,
        key="ad_copy_enabled",
    )

    if not ad_copy_enabled:
        return "", False, "preserve"

    raw_prompt = st.text_area(
        "광고 문구",
        placeholder=(
            "직접 넣고 싶은 광고 문구를 입력하세요.\n"
            "비워두면 백엔드가 기본 문구를 생성할 수 있습니다."
        ),
        height=150,
        key="ad_copy_prompt",
        help="비워두면 이미지 생성 시 백엔드가 기본 문구를 생성할 수 있습니다.",
        label_visibility="collapsed",
    )

    prompt = raw_prompt
    copy_mode_labels = [label for label, _mode in COPY_MODE_OPTIONS]
    copy_mode_by_label = dict(COPY_MODE_OPTIONS)
    copy_mode_label = st.radio(
        "광고 문구 다듬기 옵션",
        options=copy_mode_labels,
        index=0,
        horizontal=False,
        key="copy_mode_label",
    )
    copy_mode = copy_mode_by_label.get(copy_mode_label, "preserve")
    return prompt, ad_copy_enabled, copy_mode
