import streamlit as st

from frontend.core.config import (
    FORMAT_OPTIONS,
    format_size_label,
    get_detail_labels,
    get_detail_size,
)
from frontend.work.components import (
    render_channel_tabs,
    render_generation_lock_css,
    render_header,
    render_section_label,
)
from frontend.work.copy_controls import render_copy_controls
from frontend.work.generation import handle_generation_request
from frontend.work.result_panel import render_result_panel
from frontend.work.state import build_result_context, get_selected_channel, sync_result_state
from frontend.work.uploads import UPLOAD_FILE_TYPES, UPLOAD_HELP_TEXT, get_primary_uploaded_file


def render_work_page() -> None:
    render_header()
    left_col, right_col = st.columns([0.4, 0.6], gap="medium")

    with left_col:
        with st.container(border=True, key="left-options-panel"):
            st.markdown('<div class="left-options-scroll-marker"></div>', unsafe_allow_html=True)

            with st.container(key="left-upload-section"):
                render_section_label("메뉴 사진 업로드", "1.png")

                uploaded_files = st.file_uploader(
                    "메뉴 사진 업로드",
                    type=UPLOAD_FILE_TYPES,
                    help=UPLOAD_HELP_TEXT,
                    accept_multiple_files=True,
                    label_visibility="collapsed",
                )
                uploaded_file = get_primary_uploaded_file(uploaded_files)

            with st.container(key="left-channel-section"):
                render_section_label("광고 채널 선택", "2.png")
                format_label = get_selected_channel()
                render_channel_tabs(format_label)

            with st.container(key="left-type-section"):
                detail_options = get_detail_labels(format_label)
                render_section_label("광고 유형 선택", "3.png", css_class="detail-choice-label")
                detail_label = st.radio(
                    "광고 유형 선택",
                    options=detail_options,
                    horizontal=False,
                    label_visibility="collapsed",
                    key=f"detail_{FORMAT_OPTIONS[format_label]['value']}",
                )
                format_label_html = format_size_label(get_detail_size(format_label, detail_label))
                st.markdown(
                    f"""
                    <div class="format-readout">
                        <span>
                            <strong class="channel-name">{format_label}</strong>
                            <small>{detail_label}</small>
                        </span>
                        <span class="format-size">{format_label_html}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with st.container(key="left-prompt-section"):
                render_section_label("이미지 요청사항", "4.png")
                prompt = st.text_area(
                    "이미지 요청사항",
                    placeholder=(
                        "예:\n"
                        "제품을 크게 중앙에 배치해줘\n"
                        "따뜻한 색감으로 만들어줘\n"
                        "미니멀하고 프리미엄한 배경으로"
                    ),
                    height=120,
                    key="image_prompt",
                    label_visibility="collapsed",
                )
                ad_copy_prompt, ad_copy_enabled, copy_mode = render_copy_controls(
                    format_label,
                    detail_label,
                    prompt,
                )

                current_result_context = build_result_context(
                    uploaded_file,
                    prompt,
                    format_label,
                    detail_label,
                    ad_copy_prompt=ad_copy_prompt,
                    copy_mode=copy_mode,
                    ad_copy_enabled=ad_copy_enabled,
                )
                sync_result_state(current_result_context)

        st.markdown('<div class="generate-button-marker"></div>', unsafe_allow_html=True)
        generate = st.button("✦ 이미지 만들기", use_container_width=True, type="primary")

    is_generating = bool(generate and uploaded_file)

    if is_generating:
        render_generation_lock_css()

    with right_col:
        render_result_panel(
            is_generating=is_generating,
            uploaded_file=uploaded_file,
            format_label=format_label,
            detail_label=detail_label,
        )

    handle_generation_request(
        generate=generate,
        uploaded_file=uploaded_file,
        prompt=prompt,
        ad_copy_prompt=ad_copy_prompt,
        format_label=format_label,
        detail_label=detail_label,
        current_result_context=current_result_context,
        ad_copy_enabled=ad_copy_enabled,
        copy_mode=copy_mode,
    )
