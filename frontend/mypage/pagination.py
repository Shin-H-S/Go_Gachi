from math import ceil
from typing import TypeVar

T = TypeVar("T")


def page_count(total_items: int, page_size: int) -> int:
    safe_page_size = max(1, page_size)
    return max(1, ceil(max(0, total_items) / safe_page_size))


def clamp_page(page: int, total_items: int, page_size: int) -> int:
    return min(max(1, page), page_count(total_items, page_size))


def paginate_items(items: list[T], page: int, page_size: int) -> tuple[list[T], int, int]:
    current_page = clamp_page(page, len(items), page_size)
    start = (current_page - 1) * max(1, page_size)
    end = start + max(1, page_size)
    return items[start:end], current_page, page_count(len(items), page_size)


def page_status_text(*, total_items: int, current_page: int, total_pages: int) -> str:
    return f"총 {total_items}개 · {current_page} / {total_pages}"
