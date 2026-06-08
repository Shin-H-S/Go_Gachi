from html import escape

import httpx
import streamlit as st

from frontend.mypage.state import folder_choices, folder_name_by_id, format_date
from frontend.services.api_client import (
    move_generation_to_folder,
    request_asset_bytes,
    to_backend_asset_url,
)


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


@st.cache_data(show_spinner=False)
def _cached_asset_bytes(url: str) -> bytes:
    return request_asset_bytes(url)


def _render_generation_card(item: dict, folders: list[dict], access_token: str) -> None:
    request_id = str(item.get("request_id") or "")
    image_url = to_backend_asset_url(item.get("image_url"))
    preset_id = str(item.get("preset_id") or "channel")
    status = str(item.get("status") or "-")
    created_at = format_date(item.get("created_at"))
    if image_url:
        st.image(image_url, use_container_width=True)
    else:
        st.markdown('<div class="mypage-empty-thumb">이미지 없음</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="mypage-card-meta">
            <span>{escape(preset_id)}</span>
            <span>{escape(status)}</span>
        </div>
        <div class="mypage-card-date">{escape(created_at)}</div>
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
    if image_url:
        try:
            image_bytes = _cached_asset_bytes(image_url)
        except httpx.HTTPError:
            st.error("이미지를 다운로드할 수 없습니다.")
        else:
            st.download_button(
                "다운로드",
                data=image_bytes,
                file_name=_download_file_name(item),
                mime="image/png",
                use_container_width=True,
                key=f"mypage-download-{request_id}",
            )


def render_generation_grid(items: list[dict], folders: list[dict], access_token: str) -> None:
    if not items:
        st.markdown(
            """
            <div class="mypage-empty-state">
                <strong>아직 만든 이미지가 없습니다</strong>
                <span>새로 생성하기에서 첫 광고 이미지를 만들어보세요.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    st.markdown('<div class="mypage-card-grid-marker"></div>', unsafe_allow_html=True)
    columns = st.columns(3, gap="medium")
    for index, item in enumerate(items):
        with columns[index % 3]:
            with st.container(border=True):
                _render_generation_card(item, folders, access_token)
