from html import escape

import httpx
import streamlit as st

from frontend.mypage.generation_status import (
    has_generation_waiting_for_image,
    is_generation_in_progress,
    is_stale_in_progress,
)
from frontend.mypage.state import folder_choices, folder_name_by_id, format_date
from frontend.services.api_client import (
    move_generation_to_folder,
    request_asset_bytes,
    to_backend_asset_url,
)

GENERATION_CARD_COLUMNS = 4
GENERATION_CARD_HEIGHT = 330
__all__ = ["has_generation_waiting_for_image", "render_generation_grid"]


def _assign_generation_folder(
    access_token: str,
    request_id: str,
    mapping: dict[str, int | None],
    state_key: str,
) -> None:
    selected_label = st.session_state.get(state_key)
    if selected_label not in mapping:
        return
    move_generation_to_folder(access_token, request_id, mapping[selected_label])


def _download_file_name(item: dict) -> str:
    request_id = str(item.get("request_id") or "").strip()
    suffix = request_id.replace("/", "-").replace("\\", "-") or "image"
    return f"go_gachi_ad_{suffix}.png"


def _card_container_key(item: dict, index: int) -> str:
    request_id = str(item.get("request_id") or "").strip()
    suffix = request_id.replace("/", "-").replace("\\", "-") or str(index)
    return f"mypage-generation-card-{suffix}"


def _download_state_key(request_id: str) -> str:
    suffix = request_id.replace("/", "-").replace("\\", "-") or "image"
    return f"mypage-download-bytes-{suffix}"


def _download_error_key(request_id: str) -> str:
    suffix = request_id.replace("/", "-").replace("\\", "-") or "image"
    return f"mypage-download-error-{suffix}"


@st.cache_data(show_spinner=False)
def _cached_asset_bytes(url: str) -> bytes:
    return request_asset_bytes(url)


def _prepare_download(request_id: str, image_url: str) -> None:
    data_key = _download_state_key(request_id)
    error_key = _download_error_key(request_id)
    try:
        st.session_state[data_key] = _cached_asset_bytes(image_url)
        st.session_state.pop(error_key, None)
    except httpx.HTTPError:
        st.session_state.pop(data_key, None)
        st.session_state[error_key] = True


def _render_generation_card(item: dict, folders: list[dict], access_token: str) -> None:
    request_id = str(item.get("request_id") or "")
    image_url = to_backend_asset_url(item.get("image_url"))
    original_image_url = to_backend_asset_url(item.get("original_image_url"))
    preset_id = str(item.get("preset_id") or "channel")
    status = str(item.get("status") or "-")
    created_at_value = item.get("created_at")
    created_at = format_date(created_at_value)
    stale_in_progress = is_stale_in_progress(status, created_at_value)
    display_status = "timeout" if stale_in_progress else status
    if image_url:
        st.image(image_url, use_container_width=True)
    elif stale_in_progress:
        st.markdown(
            """
            <div class="mypage-stale-thumb" role="status">
                <strong>생성 시간이 초과되었습니다</strong>
                <span>다시 생성해 주세요.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif is_generation_in_progress(status):
        st.markdown(
            """
            <div class="mypage-generating-thumb" role="status" aria-live="polite">
                <div class="mypage-generating-spinner"></div>
                <strong>이미지 생성중</strong>
                <span>완료되면 이미지가 표시됩니다.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="mypage-empty-thumb">이미지 없음</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="mypage-card-meta">
            <span>{escape(preset_id)}</span>
            <span>{escape(created_at)}: {escape(display_status)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    labels, mapping = folder_choices(folders)
    current_label = folder_name_by_id(folders, item.get("folder_id"))
    select_key = f"mypage-folder-select-{request_id}"
    st.selectbox(
        "폴더 선택",
        labels,
        index=labels.index(current_label) if current_label in labels else 0,
        key=select_key,
        label_visibility="collapsed",
        on_change=_assign_generation_folder,
        args=(access_token, request_id, mapping, select_key),
    )
    original_col, download_col = st.columns(2, gap="small")
    with original_col:
        if original_image_url:
            st.link_button(
                "원본",
                original_image_url,
                key=f"mypage-original-{request_id}",
                use_container_width=True,
            )
        else:
            st.button(
                "원본",
                disabled=True,
                key=f"mypage-original-{request_id}",
                use_container_width=True,
            )
    data_key = _download_state_key(request_id)
    error_key = _download_error_key(request_id)
    if st.session_state.get(error_key):
        st.error("이미지를 다운로드할 수 없습니다.")

    with download_col:
        download_data = st.session_state.get(data_key)
        if isinstance(download_data, bytes):
            st.download_button(
                "다운로드",
                data=download_data,
                file_name=_download_file_name(item),
                mime="image/png",
                use_container_width=True,
                key=f"mypage-download-{request_id}",
            )
        else:
            st.button(
                "다운로드",
                disabled=not image_url,
                key=f"mypage-download-{request_id}",
                use_container_width=True,
                on_click=_prepare_download if image_url else None,
                args=(request_id, image_url) if image_url else None,
            )


def render_generation_grid(items: list[dict], folders: list[dict], access_token: str) -> None:
    if not items:
        st.markdown(
            """
            <div class="mypage-empty-state">
                <strong>아직 만든 이미지가 없습니다</strong>
                <span>작업 페이지로 돌아가 첫 광고 이미지를 만들어보세요.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    st.markdown('<div class="mypage-card-grid-marker"></div>', unsafe_allow_html=True)
    columns = st.columns(GENERATION_CARD_COLUMNS, gap="medium")
    for index, item in enumerate(items):
        with columns[index % GENERATION_CARD_COLUMNS]:
            with st.container(
                border=True,
                height=GENERATION_CARD_HEIGHT,
                key=_card_container_key(item, index),
            ):
                _render_generation_card(item, folders, access_token)
