import httpx
import streamlit as st

from frontend.mypage.cache import clear_mypage_cache
from frontend.mypage.state import FOLDER_NONE_VIEW, folder_view, selected_folder_id, set_view
from frontend.services.api_client import delete_my_folder, rename_my_folder

FOLDER_DELETE_CONFIRM_KEY = "mypage_delete_folder_confirm_id"


def _folder_error_detail(exc: httpx.HTTPStatusError, fallback: str) -> str:
    try:
        detail = exc.response.json().get("detail")
    except ValueError:
        detail = None
    if exc.response.status_code == 404 and detail == "Not Found":
        return (
            "백엔드 서버가 폴더 이름변경/삭제 API를 아직 반영하지 않았습니다. "
            "백엔드를 재시작한 뒤 다시 시도해주세요."
        )
    return str(detail or fallback)


def _render_folder_rename_form(access_token: str, folder_id: int, folder_name: str) -> None:
    with st.form(f"mypage-rename-folder-form-{folder_id}", clear_on_submit=False):
        new_name = st.text_input(
            "폴더명",
            value=folder_name,
            key=f"mypage-rename-folder-name-{folder_id}",
            label_visibility="collapsed",
        )
        submit = st.form_submit_button("이름변경", use_container_width=True)
        if submit:
            try:
                rename_my_folder(access_token, folder_id, new_name)
            except httpx.HTTPStatusError as exc:
                st.error(_folder_error_detail(exc, "폴더명을 변경하지 못했습니다."))
            else:
                clear_mypage_cache()
                st.rerun()


def _render_folder_management_menu(access_token: str, folder_id: int, folder_name: str) -> None:
    with st.popover("⋯", key=f"mypage-folder-menu-{folder_id}", use_container_width=True):
        _render_folder_rename_form(access_token, folder_id, folder_name)
        if st.button(
            "폴더 삭제",
            key=f"mypage-delete-folder-{folder_id}",
            use_container_width=True,
        ):
            st.session_state[FOLDER_DELETE_CONFIRM_KEY] = folder_id
            st.rerun()


def _render_delete_folder_confirmation_content(access_token: str, folder_id: int) -> None:
    st.warning("폴더만 삭제되며, 폴더 안 이미지는 미분류로 이동됩니다.")
    confirm_col, cancel_col = st.columns(2, gap="small")
    with confirm_col:
        if st.button(
            "폴더 삭제",
            key=f"mypage-confirm-delete-folder-{folder_id}",
            use_container_width=True,
        ):
            try:
                delete_my_folder(access_token, folder_id)
            except httpx.HTTPStatusError as exc:
                st.error(_folder_error_detail(exc, "폴더를 삭제하지 못했습니다."))
            else:
                clear_mypage_cache()
                st.session_state.pop(FOLDER_DELETE_CONFIRM_KEY, None)
                set_view(FOLDER_NONE_VIEW)
                st.rerun()
    with cancel_col:
        if st.button(
            "취소",
            key=f"mypage-cancel-delete-folder-{folder_id}",
            use_container_width=True,
        ):
            st.session_state.pop(FOLDER_DELETE_CONFIRM_KEY, None)
            st.rerun()


def _render_delete_folder_confirmation(access_token: str, folder_id: int) -> None:
    if st.session_state.get(FOLDER_DELETE_CONFIRM_KEY) != folder_id:
        return

    dialog = getattr(st, "dialog", None)
    if dialog is None:
        with st.container(key=f"mypage-delete-folder-confirm-{folder_id}"):
            _render_delete_folder_confirmation_content(access_token, folder_id)
        return

    @dialog("폴더 삭제")
    def confirm_delete_dialog() -> None:
        _render_delete_folder_confirmation_content(access_token, folder_id)

    confirm_delete_dialog()


def render_folder_row(
    folder: dict,
    *,
    view: str,
    access_token: str,
    sidebar_button_marker,
) -> None:
    folder_id = int(folder["id"])
    folder_name = str(folder["name"])
    is_selected = selected_folder_id(view) == folder_id

    if not is_selected:
        sidebar_button_marker()
        if st.button(folder_name, key=f"mypage-folder-{folder_id}", use_container_width=True):
            set_view(folder_view(folder_id))
            st.rerun()
        return

    with st.container(key=f"mypage-folder-row-{folder_id}"):
        folder_col, menu_col = st.columns([0.78, 0.22], gap="small")
        with folder_col:
            sidebar_button_marker()
            if st.button(folder_name, key=f"mypage-folder-{folder_id}", use_container_width=True):
                set_view(folder_view(folder_id))
                st.rerun()
        with menu_col:
            _render_folder_management_menu(access_token, folder_id, folder_name)
    _render_delete_folder_confirmation(access_token, folder_id)
