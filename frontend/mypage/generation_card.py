import re
from html import escape

import streamlit as st

from frontend.mypage.generation_status import (
    generation_status_badge,
    has_generation_waiting_for_image,
    is_generation_in_progress,
    is_stale_in_progress,
)
from frontend.mypage.selection import selected_generation_ids, toggle_generation_selection
from frontend.mypage.state import folder_name_by_id, format_date
from frontend.services.api_client import to_backend_asset_url

GENERATION_CARD_COLUMNS = 4
GENERATION_CARD_HEIGHT = 330
__all__ = ["has_generation_waiting_for_image", "render_generation_grid"]


def _card_container_key(item: dict, index: int, *, selected: bool = False) -> str:
    request_id = str(item.get("request_id") or "").strip()
    suffix = request_id.replace("/", "-").replace("\\", "-") or str(index)
    state_part = "selected-" if selected else ""
    return f"mypage-generation-card-{state_part}{suffix}"


def _folder_name_for_generation(item: dict, folders: list[dict]) -> str:
    folder_id = item.get("folder_id")
    if folder_id is not None:
        try:
            folder_id = int(folder_id)
        except (TypeError, ValueError):
            pass
    return folder_name_by_id(folders, folder_id)


def _image_modal_id(request_id: str) -> str:
    safe_id = re.sub(r"[^0-9A-Za-z_-]+", "-", request_id).strip("-")
    return f"mypage-image-modal-{safe_id or 'image'}"


def _render_generation_image(image_url: str, request_id: str) -> None:
    modal_id = _image_modal_id(request_id)
    safe_url = escape(image_url, quote=True)
    safe_alt = escape(f"{request_id or 'generated'} image", quote=True)
    st.markdown(
        f"""
        <div class="mypage-image-preview">
            <input class="mypage-image-modal-toggle" id="{modal_id}" type="checkbox" />
            <label class="mypage-image-thumb" for="{modal_id}" aria-label="생성 이미지 크게 보기">
                <img src="{safe_url}" alt="{safe_alt}" />
            </label>
            <label class="mypage-image-modal" for="{modal_id}" aria-label="확대 이미지 닫기">
                <img src="{safe_url}" alt="{safe_alt}" />
            </label>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_generation_card(
    item: dict,
    folders: list[dict],  # noqa: ARG001
    access_token: str,  # noqa: ARG001
    *,
    selected: bool = False,
) -> None:
    request_id = str(item.get("request_id") or "")
    image_url = to_backend_asset_url(item.get("image_url"))
    preset_id = str(item.get("preset_id") or "channel")
    status = str(item.get("status") or "-")
    created_at_value = item.get("created_at")
    created_at = format_date(created_at_value)
    stale_in_progress = is_stale_in_progress(status, created_at_value)
    status_label, status_kind = generation_status_badge(status, created_at_value)
    folder_name = _folder_name_for_generation(item, folders)

    if image_url:
        _render_generation_image(image_url, request_id)
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
            <span class="mypage-card-identity">
                {escape(preset_id)} {escape(created_at)}
                <span class="mypage-status-badge mypage-status-{escape(status_kind)}">
                    {escape(status_label)}
                </span>
            </span>
            <span class="mypage-card-folder">폴더: {escape(folder_name)}</span>
        </div>
        <div class="mypage-card-select-zone"></div>
        """,
        unsafe_allow_html=True,
    )
    st.button(
        "선택 해제" if selected else "선택",
        key=f"mypage-select-{request_id}",
        use_container_width=True,
        on_click=toggle_generation_selection,
        args=(st.session_state, request_id),
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
    selected_ids = set(selected_generation_ids(st.session_state))
    for index, item in enumerate(items):
        request_id = str(item.get("request_id") or "")
        selected = request_id in selected_ids
        with columns[index % GENERATION_CARD_COLUMNS]:
            with st.container(
                border=True,
                height=GENERATION_CARD_HEIGHT,
                key=_card_container_key(item, index, selected=selected),
            ):
                _render_generation_card(item, folders, access_token, selected=selected)
