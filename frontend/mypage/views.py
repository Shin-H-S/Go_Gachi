from html import escape

import streamlit as st

from frontend.auth.session import clear_auth_session
from frontend.core.router import navigate_to
from frontend.mypage.components import render_generation_grid
from frontend.mypage.pagination import page_count, page_status_text, paginate_items
from frontend.mypage.state import filter_generations, format_date, profile_name
from frontend.services.api_client import data_url_to_bytes, to_backend_asset_url

GENERATION_PAGE_SIZE = 12
UPLOAD_PAGE_SIZE = 8


def _page_key(scope: str) -> str:
    safe_scope = scope.replace(":", "_").replace("/", "_")
    return f"mypage_page_{safe_scope}"


def _current_page(scope: str) -> int:
    try:
        return int(st.session_state.get(_page_key(scope), 1))
    except (TypeError, ValueError):
        return 1


def current_page(scope: str) -> int:
    return _current_page(scope)


def _render_collection_status(total_items: int, current_page: int, total_pages: int) -> None:
    status = page_status_text(
        total_items=total_items,
        current_page=current_page,
        total_pages=total_pages,
    )
    st.markdown(
        f'<div class="mypage-list-status">{escape(status)}</div>',
        unsafe_allow_html=True,
    )


def render_pagination_controls(scope: str, current_page: int, total_pages: int) -> None:
    if total_pages <= 1:
        return
    previous_col, status_col, next_col = st.columns([0.24, 0.52, 0.24], gap="small")
    key = _page_key(scope)
    with previous_col:
        if st.button(
            "이전", disabled=current_page <= 1, key=f"{key}-prev", use_container_width=True
        ):
            st.session_state[key] = max(1, current_page - 1)
            st.rerun()
    with status_col:
        st.markdown(
            f'<div class="mypage-pagination-status">{current_page} / {total_pages}</div>',
            unsafe_allow_html=True,
        )
    with next_col:
        if st.button(
            "다음",
            disabled=current_page >= total_pages,
            key=f"{key}-next",
            use_container_width=True,
        ):
            st.session_state[key] = min(total_pages, current_page + 1)
            st.rerun()


def render_recent_work(
    generations: list[dict],
    folders: list[dict],
    access_token: str,
    *,
    total_count: int | None = None,
    current_page: int | None = None,
) -> None:
    total_items = len(generations) if total_count is None else max(0, int(total_count))
    total_pages = page_count(total_items, GENERATION_PAGE_SIZE)
    visible_page = current_page if current_page is not None else _current_page("recent")
    visible_page = min(max(1, int(visible_page)), total_pages)
    _render_collection_status(total_items, visible_page, total_pages)
    render_generation_grid(generations, folders, access_token)
    render_pagination_controls("recent", visible_page, total_pages)


def render_folder_view(
    view: str,
    generations: list[dict],
    folders: list[dict],
    access_token: str,
) -> None:
    filtered = filter_generations(generations, view)
    items, current_page, total_pages = paginate_items(
        filtered,
        _current_page(view),
        GENERATION_PAGE_SIZE,
    )
    _render_collection_status(len(filtered), current_page, total_pages)
    render_generation_grid(items, folders, access_token)
    render_pagination_controls(view, current_page, total_pages)


def render_uploads(uploads: list[dict]) -> None:
    if not uploads:
        st.markdown(
            """
            <div class="mypage-empty-state">
                <strong>업로드한 원본 이미지가 없습니다</strong>
                <span>작업 페이지에서 원본 이미지를 올리면 여기에 모입니다.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    total_uploads = len(uploads)
    visible_uploads, current_page, total_pages = paginate_items(
        uploads,
        _current_page("uploads"),
        UPLOAD_PAGE_SIZE,
    )
    _render_collection_status(total_uploads, current_page, total_pages)
    columns = st.columns(4, gap="medium")
    for index, item in enumerate(visible_uploads):
        image_url = to_backend_asset_url(item.get("original_image_url"))
        image_data_url = str(item.get("image_data_url") or "")
        with columns[index % 4]:
            with st.container(border=True):
                if image_url:
                    st.image(image_url, use_container_width=True)
                elif image_data_url:
                    st.image(data_url_to_bytes(image_data_url), use_container_width=True)
                else:
                    st.markdown(
                        '<div class="mypage-empty-thumb">이미지 없음</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f"""
                    <div class="mypage-card-meta">
                        <span>{escape(format_date(item.get("created_at")))}</span>
                        <span>{int(item.get("used_count") or 0)}회 사용</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    render_pagination_controls("uploads", current_page, total_pages)


def render_account_settings(profile: dict) -> None:
    display_name = profile_name(profile)
    st.markdown(
        f"""
        <div class="mypage-account-panel">
            <div>
                <span>닉네임</span>
                <strong>{escape(display_name)}</strong>
            </div>
            <div>
                <span>이메일</span>
                <strong>{escape(str(profile.get("email") or "-"))}</strong>
            </div>
            <div>
                <span>권한</span>
                <strong>{escape(str(profile.get("role") or "user"))}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("로그아웃", key="mypage-logout", use_container_width=False):
        clear_auth_session(st.session_state, "로그아웃되었습니다.")
        navigate_to("main")
        st.rerun()
