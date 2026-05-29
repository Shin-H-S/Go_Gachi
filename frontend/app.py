import time
from html import escape

import httpx
import streamlit as st
from api_client import BACKEND_URL, build_feedback, request_backend
from image_utils import bytes_to_data_url, create_mock_banner, make_preview_canvas
from styles import add_css
from upload_utils import get_primary_uploaded_file

from config import (
    CHANNEL_SLUGS,
    FORMAT_OPTIONS,
    format_size_label,
    get_detail_labels,
    get_detail_size,
    get_existing_channel_asset_path,
)

st.set_page_config(
    page_title="Cafe Ad Maker",
    page_icon="CA",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def compact_html(html: str) -> str:
    return " ".join(line.strip() for line in html.strip().splitlines() if line.strip())


def render_preview_shell(
    format_label: str,
    body_html: str,
    detail_label: str | None = None,
) -> None:
    body = compact_html(body_html)
    caption = f"{format_label} · {detail_label}" if detail_label else format_label
    size_label = (
        format_size_label(get_detail_size(format_label, detail_label)) if detail_label else ""
    )
    st.markdown(
        (
            '<div class="preview-shell">'
            '<div class="result-caption">'
            f"<span>{caption}</span>"
            f"<span>{size_label}</span>"
            "</div>"
            f"{body}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_image_preview(
    image_bytes: bytes,
    format_label: str,
    detail_label: str | None = None,
) -> None:
    preview_bytes = make_preview_canvas(image_bytes, format_label, detail_label)
    preview_src = bytes_to_data_url(preview_bytes)
    render_preview_shell(
        format_label,
        f"""
        <div class="preview-image-frame">
            <img src="{preview_src}" alt="미리보기 이미지" />
        </div>
        """,
        detail_label,
    )


def get_selected_channel() -> str:
    selected_label = st.session_state.get("selected_channel", "인스타그램")
    if selected_label not in FORMAT_OPTIONS:
        selected_label = "인스타그램"
        st.session_state["selected_channel"] = selected_label

    return selected_label


def render_channel_tabs(selected_label: str) -> None:
    st.markdown('<div class="channel-button-marker"></div>', unsafe_allow_html=True)
    columns = st.columns(3, gap="small")

    for column, label in zip(columns, FORMAT_OPTIONS.keys(), strict=True):
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


add_css()
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
            type=["jpg", "jpeg", "png", "webp"],
            help="JPG, PNG, WEBP 파일을 업로드할 수 있습니다.",
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        uploaded_file = get_primary_uploaded_file(uploaded_files)

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
            height=150,
            label_visibility="collapsed",
        )

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

is_generating = bool(generate and uploaded_file and prompt.strip())

if is_generating:
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
                + div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-primary"] {
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

with right_col:
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

if generate:
    if not uploaded_file:
        st.warning("메뉴 사진을 먼저 업로드해주세요.")
    elif not prompt.strip():
        st.warning("프롬프트를 입력해주세요.")
    else:
        try:
            time.sleep(1.2)
            if BACKEND_URL:
                result_bytes = request_backend(
                    uploaded_file,
                    prompt.strip(),
                    format_label,
                    detail_label,
                )
            else:
                result_bytes = create_mock_banner(
                    image_bytes=uploaded_file.getvalue(),
                    prompt=build_feedback(prompt.strip(), detail_label),
                    format_label=format_label,
                    detail_label=detail_label,
                )
            st.session_state["result_bytes"] = result_bytes
            st.rerun()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            st.error(f"백엔드 생성 요청에 실패했습니다. ({exc.response.status_code}) {detail}")
        except httpx.HTTPError as exc:
            st.error(f"백엔드에 연결할 수 없습니다: {exc}")
        except Exception as exc:
            st.error(f"이미지 생성 중 오류가 발생했습니다: {exc}")
