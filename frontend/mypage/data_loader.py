"""마이페이지에서 백엔드 generation 데이터를 페이지 단위로 불러오는 로더."""

from collections.abc import Callable

from frontend.mypage import views
from frontend.mypage.pagination import page_count

BACKEND_GENERATION_PAGE_SIZE = 12
RequestFn = Callable[..., dict]


def _safe_page(value: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return 1


def load_generation_pages(
    request_fn: RequestFn,
    access_token: str,
) -> tuple[list[dict], int]:
    """백엔드 페이지를 전부 순회해 generation 목록과 총 개수를 모은다."""
    generations: list[dict] = []
    page = 1
    total_count = 0
    while True:
        payload = request_fn(access_token, page=page)
        items = list(payload.get("items", []))
        if page == 1:
            total_count = int(payload.get("total_count") or len(items))
        generations.extend(items)
        if not items or len(generations) >= total_count:
            return generations, total_count
        page += 1


def _load_slice(
    request_fn: RequestFn,
    access_token: str,
    page: int,
    *,
    folder_id: int | None = None,
) -> tuple[list[dict], int]:
    page = _safe_page(page)
    start = (page - 1) * views.GENERATION_PAGE_SIZE
    end = start + views.GENERATION_PAGE_SIZE
    first_backend_page = (start // BACKEND_GENERATION_PAGE_SIZE) + 1
    first_payload = request_fn(access_token, page=first_backend_page, folder_id=folder_id)
    first_items = list(first_payload.get("items", []))
    total_count = int(first_payload.get("total_count") or (start + len(first_items)))
    combined_items = first_items
    effective_end = min(end, total_count)
    last_backend_page = (
        ((effective_end - 1) // BACKEND_GENERATION_PAGE_SIZE) + 1
        if effective_end > start
        else first_backend_page
    )
    for backend_page in range(first_backend_page + 1, last_backend_page + 1):
        payload = request_fn(access_token, page=backend_page, folder_id=folder_id)
        combined_items.extend(list(payload.get("items", [])))
    offset = start - (first_backend_page - 1) * BACKEND_GENERATION_PAGE_SIZE
    return combined_items[offset : offset + views.GENERATION_PAGE_SIZE], total_count


def load_recent_generation_page(
    request_fn: RequestFn,
    access_token: str,
    page: int,
    *,
    folder_id: int | None = None,
) -> tuple[list[dict], int, int]:
    """요청 페이지에 해당하는 슬라이스 + 총 개수 + 보정된 현재 페이지를 반환한다."""
    requested_page = _safe_page(page)
    generations, total_count = _load_slice(
        request_fn,
        access_token,
        requested_page,
        folder_id=folder_id,
    )
    current_page = min(requested_page, page_count(total_count, views.GENERATION_PAGE_SIZE))
    if current_page != requested_page:
        generations, total_count = _load_slice(
            request_fn,
            access_token,
            current_page,
            folder_id=folder_id,
        )
    return generations, total_count, current_page
