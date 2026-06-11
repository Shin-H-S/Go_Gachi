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
)
from frontend.work.copy_controls import render_copy_controls
from frontend.work.generation import handle_generation_request
from frontend.work.logo_controls import render_logo_controls, render_logo_preview
from frontend.work.result_panel import render_result_panel
from frontend.work.state import build_result_context, get_selected_channel, sync_result_state
from frontend.work.uploads import UPLOAD_FILE_TYPES, UPLOAD_HELP_TEXT, get_primary_uploaded_file


def render_work_page() -> None:
    render_header()
    left_col, right_col = st.columns([0.38, 0.62], gap="large")

    with left_col:
        with st.container(border=True, key="left-upload-section"):
            st.markdown(
                """
                <p class="section-label">메뉴 사진 업로드</p>
                """,
                unsafe_allow_html=True,
            )

            uploaded_files = st.file_uploader(
                "메뉴 사진 업로드",
                type=UPLOAD_FILE_TYPES,
                help=UPLOAD_HELP_TEXT,
                accept_multiple_files=True,
                label_visibility="collapsed",
            )
            uploaded_file = get_primary_uploaded_file(uploaded_files)

        logo_controls_col, logo_preview_col = st.columns([0.52, 0.48], gap="small")
        with logo_controls_col:
            with st.container(border=True, key="left-logo-section"):
                logo_file, logo_position = render_logo_controls()
        with logo_preview_col:
            with st.container(border=True, key="left-logo-preview-section"):
                render_logo_preview(logo_file)

        with st.container(border=True, key="left-channel-section"):
            st.markdown('<p class="section-label">광고 채널 선택</p>', unsafe_allow_html=True)
            format_label = get_selected_channel()
            render_channel_tabs(format_label)

        with st.container(border=True, key="left-type-section"):
            detail_options = get_detail_labels(format_label)
            st.markdown('<p class="detail-choice-label">광고 유형 선택</p>', unsafe_allow_html=True)
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

        with st.container(border=True, key="left-prompt-section"):
            st.markdown('<p class="section-label">프롬프트</p>', unsafe_allow_html=True)
            prompt = st.text_area(
                "프롬프트",
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
                logo_file=logo_file,
                logo_position=logo_position,
            )
            sync_result_state(current_result_context)

            st.markdown('<div class="generate-button-marker"></div>', unsafe_allow_html=True)
            generate = st.button("✦ 이미지 만들기", use_container_width=True, type="primary")

            st.markdown('<div class="tool-row">', unsafe_allow_html=True)
            undo_col, redo_col, save_col = st.columns(3, gap="small")
            with undo_col:
                undo_clicked = st.button("↶", help="되돌리기", use_container_width=True)
            with redo_col:
                redo_clicked = st.button("↷", help="다시 실행", use_container_width=True)
            with save_col:
                if "result_bytes" in st.session_state:
                    st.download_button(
                        "💾",
                        data=st.session_state["result_bytes"],
                        file_name="cafe_ad_maker_result.png",
                        mime="image/png",
                        help="저장",
                        use_container_width=True,
                    )
                else:
                    save_clicked = st.button("💾", help="저장", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if undo_clicked:
            st.info("되돌릴 이전 결과가 아직 없습니다.")
        if redo_clicked:
            st.info("다시 실행할 다음 결과가 아직 없습니다.")
        if "result_bytes" not in st.session_state and "save_clicked" in locals() and save_clicked:
            st.info("저장할 결과 이미지를 먼저 만들어주세요.")

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
        logo_file=logo_file,
        logo_position=logo_position,
        prompt=prompt,
        ad_copy_prompt=ad_copy_prompt,
        format_label=format_label,
        detail_label=detail_label,
        current_result_context=current_result_context,
        ad_copy_enabled=ad_copy_enabled,
        copy_mode=copy_mode,
    )
