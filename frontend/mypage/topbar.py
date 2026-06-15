from html import escape
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
import streamlit as st

from frontend.core.router import navigate_to
from frontend.mypage.selection import (
    action_availability,
    selected_generation_ids,
    selected_generation_items,
)
from frontend.mypage.state import (
    FOLDER_PREFIX,
    filter_generations,
    folder_choices,
    folder_name_by_id,
)
from frontend.services.api_client import (
    move_generation_to_folder,
    request_asset_bytes,
    to_backend_asset_url,
)


@st.cache_data(show_spinner=False)
def _cached_asset_bytes(url: str) -> bytes:
    return request_asset_bytes(url)


def _download_file_name(item: dict) -> str:
    request_id = str(item.get("request_id") or "").strip()
    suffix = request_id.replace("/", "-").replace("\\", "-") or "image"
    return f"go_gachi_ad_{suffix}.png"


def _download_payload(items: list[dict]) -> tuple[bytes, str, str, bool]:
    downloadable = [
        (item, to_backend_asset_url(item.get("image_url")))
        for item in items
        if to_backend_asset_url(item.get("image_url"))
    ]
    if not downloadable:
        return b"", "go_gachi_ad_image.png", "image/png", True
    if len(downloadable) == 1:
        item, image_url = downloadable[0]
        return _cached_asset_bytes(str(image_url)), _download_file_name(item), "image/png", False

    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for item, image_url in downloadable:
            archive.writestr(_download_file_name(item), _cached_asset_bytes(str(image_url)))
    return buffer.getvalue(), "go_gachi_selected_images.zip", "application/zip", False


def _visible_selected_items(view: str, generations: list[dict]) -> list[dict]:
    return selected_generation_items(
        filter_generations(generations, view),
        selected_generation_ids(st.session_state),
    )


def _render_original_action(selected_items: list[dict], *, enabled: bool) -> None:
    original_url = (
        to_backend_asset_url(selected_items[0].get("original_image_url")) if enabled else None
    )
    if original_url:
        st.link_button(
            "원본 보기", original_url, key="mypage-action-original", use_container_width=True
        )
        return
    st.button("원본 보기", key="mypage-action-original", disabled=True, use_container_width=True)


def _render_download_action(selected_items: list[dict], *, enabled: bool) -> None:
    data, file_name, mime, disabled = b"", "go_gachi_ad_image.png", "image/png", not enabled
    if enabled:
        try:
            data, file_name, mime, disabled = _download_payload(selected_items)
        except httpx.HTTPError:
            disabled = True
            st.error("이미지를 다운로드할 수 없습니다.")
    st.download_button(
        "다운로드",
        data=data,
        file_name=file_name,
        mime=mime,
        key="mypage-action-download",
        disabled=disabled,
        use_container_width=True,
    )


def _folder_select_value(
    *,
    folders: list[dict],
    selected_items: list[dict],
    enabled: bool,
) -> tuple[str, dict[str, int | None], dict]:
    labels, mapping = folder_choices(folders)
    selected_item = selected_items[0] if enabled else {}
    current_label = folder_name_by_id(folders, selected_item.get("folder_id"))
    selected_label = st.selectbox(
        "폴더 선택",
        options=labels,
        index=labels.index(current_label) if current_label in labels else 0,
        key="mypage-action-folder-select",
        disabled=not enabled,
        label_visibility="collapsed",
    )
    return str(selected_label), mapping, selected_item


def _render_folder_action(
    *,
    access_token: str,
    selected_label: str,
    mapping: dict[str, int | None],
    selected_item: dict,
    enabled: bool,
) -> None:
    if not st.button(
        "폴더 설정", key="mypage-action-folder", disabled=not enabled, use_container_width=True
    ):
        return
    request_id = str(selected_item.get("request_id") or "")
    move_generation_to_folder(access_token, request_id, mapping[selected_label])
    st.rerun()


def _render_selection_actions(
    *,
    view: str,
    access_token: str,
    generations: list[dict],
    folders: list[dict],
) -> None:
    selected_items = _visible_selected_items(view, generations)
    availability = action_availability(len(selected_items))
    st.markdown('<div class="mypage-selection-actions-marker"></div>', unsafe_allow_html=True)

    action_cols = st.columns([1, 1, 1, 1.05], gap="small")
    with action_cols[3]:
        selected_label, mapping, selected_item = _folder_select_value(
            folders=folders,
            selected_items=selected_items,
            enabled=availability["single"],
        )
    with action_cols[0]:
        _render_original_action(selected_items, enabled=availability["single"])
    with action_cols[1]:
        _render_download_action(selected_items, enabled=availability["download"])
    with action_cols[2]:
        _render_folder_action(
            access_token=access_token,
            selected_label=selected_label,
            mapping=mapping,
            selected_item=selected_item,
            enabled=availability["single"],
        )


def render_topbar(
    view: str,
    title: str,
    access_token: str,
    *,
    generations: list[dict] | None = None,
    folders: list[dict] | None = None,
) -> None:
    title_col, action_col = st.columns([0.58, 0.42], gap="large")
    with title_col:
        st.markdown(f'<h1 class="mypage-title">{escape(title)}</h1>', unsafe_allow_html=True)
    with action_col:
        button_key = (
            "mypage-new-work"
            if view.startswith(FOLDER_PREFIX)
            else "mypage-new-work-simple"
        )
        if st.button("작업페이지로 돌아가기", key=button_key, use_container_width=True):
            navigate_to("work")
            st.rerun()
        _render_selection_actions(
            view=view,
            access_token=access_token,
            generations=generations or [],
            folders=folders or [],
        )
