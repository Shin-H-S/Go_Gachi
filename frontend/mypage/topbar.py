from html import escape

import streamlit as st

from frontend.core.router import navigate_to
from frontend.mypage.download_actions import render_download_action
from frontend.mypage.pagination import paginate_items
from frontend.mypage.selection import (
    action_availability,
    all_generation_page_items_selected,
    selected_generation_ids,
    selected_generation_items,
    toggle_generation_page_selection,
)
from frontend.mypage.state import (
    FOLDER_PREFIX,
    RECENT_VIEW,
    filter_generations,
    folder_choices,
    folder_name_by_id,
)
from frontend.mypage.work_handoff import (
    generation_work_image_url,
    prepare_generation_for_work,
)
from frontend.services.api_client import (
    move_generation_to_folder,
    to_backend_asset_url,
)

GENERATION_PAGE_SIZE = 12
WORK_FROM_IMAGE_LABEL = "↪ 이어작업"
ORIGINAL_LABEL = "⌕ 원본보기"
FOLDER_ACTION_LABEL = "⇄ 폴더변경"


def _page_key(scope: str) -> str:
    safe_scope = scope.replace(":", "_").replace("/", "_")
    return f"mypage_page_{safe_scope}"


def _current_page(scope: str) -> int:
    try:
        return int(st.session_state.get(_page_key(scope), 1))
    except (TypeError, ValueError):
        return 1


def _current_page_items(view: str, generations: list[dict]) -> list[dict]:
    filtered = filter_generations(generations, view)
    if view == RECENT_VIEW:
        return filtered
    items, _, _ = paginate_items(filtered, _current_page(view), GENERATION_PAGE_SIZE)
    return items


def _render_select_all_action(page_items: list[dict]) -> None:
    is_active = all_generation_page_items_selected(st.session_state, page_items)
    if st.button(
        "전체 선택",
        key="mypage-action-select-all-active" if is_active else "mypage-action-select-all",
        disabled=not page_items,
        use_container_width=True,
    ):
        toggle_generation_page_selection(st.session_state, page_items)
        st.rerun()


def _render_original_action(selected_items: list[dict], *, enabled: bool) -> None:
    original_image_url = selected_items[0].get("original_image_url") if enabled else None
    original_url = to_backend_asset_url(original_image_url)
    if original_url:
        st.link_button(
            ORIGINAL_LABEL, original_url, key="mypage-action-original", use_container_width=True
        )
        return
    st.button(ORIGINAL_LABEL, key="mypage-action-original", disabled=True, use_container_width=True)


def _render_work_from_image_action(selected_items: list[dict], *, enabled: bool) -> None:
    selected_item = selected_items[0] if enabled else {}
    can_open = bool(generation_work_image_url(selected_item))
    if not st.button(
        WORK_FROM_IMAGE_LABEL,
        key="mypage-action-work-from-image",
        disabled=not can_open,
        use_container_width=True,
    ):
        return
    if not prepare_generation_for_work(st.session_state, selected_item):
        return
    navigate_to("work")
    st.rerun()


def _folder_select_value(
    *,
    folders: list[dict],
    selected_items: list[dict],
    enabled: bool,
) -> tuple[str, dict[str, int | None]]:
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
    return str(selected_label), mapping


def _render_folder_action(
    *,
    access_token: str,
    selected_label: str,
    mapping: dict[str, int | None],
    selected_items: list[dict],
    enabled: bool,
) -> None:
    if not st.button(
        FOLDER_ACTION_LABEL,
        key="mypage-action-folder",
        disabled=not enabled,
        use_container_width=True,
    ):
        return
    if selected_label not in mapping:
        return
    for item in selected_items:
        request_id = str(item.get("request_id") or "")
        if request_id:
            move_generation_to_folder(access_token, request_id, mapping[selected_label])
    st.rerun()


def _render_selection_actions(
    *,
    view: str,
    access_token: str,
    generations: list[dict],
    folders: list[dict],
) -> None:
    page_items = _current_page_items(view, generations)
    selected_items = selected_generation_items(
        page_items,
        selected_generation_ids(st.session_state),
    )
    availability = action_availability(len(selected_items))
    st.markdown('<div class="mypage-selection-actions-marker"></div>', unsafe_allow_html=True)

    action_cols = st.columns([1, 1, 1, 1, 1.05], gap="small")
    with action_cols[4]:
        selected_label, mapping = _folder_select_value(
            folders=folders,
            selected_items=selected_items,
            enabled=availability["folder"],
        )
    with action_cols[0]:
        _render_work_from_image_action(selected_items, enabled=availability["single"])
    with action_cols[1]:
        _render_original_action(selected_items, enabled=availability["single"])
    with action_cols[2]:
        render_download_action(selected_items, enabled=availability["download"])
    with action_cols[3]:
        _render_folder_action(
            access_token=access_token,
            selected_label=selected_label,
            mapping=mapping,
            selected_items=selected_items,
            enabled=availability["folder"],
        )


def render_topbar(
    view: str,
    title: str,
    access_token: str,
    *,
    generations: list[dict] | None = None,
    folders: list[dict] | None = None,
) -> None:
    title_col, action_col = st.columns([0.46, 0.54], gap="large")
    with title_col:
        st.markdown(f'<h1 class="mypage-title">{escape(title)}</h1>', unsafe_allow_html=True)
        _render_select_all_action(_current_page_items(view, generations or []))
    with action_col:
        button_key = "mypage-new-work-simple"
        if view.startswith(FOLDER_PREFIX):
            button_key = "mypage-new-work"
        if st.button("작업페이지로 돌아가기", key=button_key, use_container_width=True):
            navigate_to("work")
            st.rerun()
        _render_selection_actions(
            view=view,
            access_token=access_token,
            generations=generations or [],
            folders=folders or [],
        )
