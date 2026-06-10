from frontend.mypage import views
from frontend.mypage.pagination import page_count, page_status_text, paginate_items
from frontend.pages import mypage as mypage_page


class FakeStreamlit:
    def __init__(self, session_state: dict[str, object] | None = None) -> None:
        self.session_state = session_state or {}
        self.markdowns: list[str] = []

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        assert unsafe_allow_html is True
        self.markdowns.append(body)


def test_page_count_keeps_empty_collections_on_one_page() -> None:
    assert page_count(0, 9) == 1
    assert page_count(1, 9) == 1
    assert page_count(10, 9) == 2


def test_paginate_items_clamps_page_and_returns_visible_items() -> None:
    items = [{"id": index} for index in range(12)]

    first_page, current_page, total_pages = paginate_items(items, page=0, page_size=5)
    last_page, last_current_page, last_total_pages = paginate_items(items, page=9, page_size=5)

    assert [item["id"] for item in first_page] == [0, 1, 2, 3, 4]
    assert current_page == 1
    assert total_pages == 3
    assert [item["id"] for item in last_page] == [10, 11]
    assert last_current_page == 3
    assert last_total_pages == 3


def test_page_status_text_includes_total_and_current_page() -> None:
    assert page_status_text(total_items=24, current_page=2, total_pages=3) == "총 24개 · 2 / 3"


def test_load_generation_pages_fetches_until_backend_total_count(monkeypatch) -> None:
    calls: list[int] = []
    pages = {
        1: {"items": [{"request_id": "a"}, {"request_id": "b"}], "total_count": 5},
        2: {"items": [{"request_id": "c"}, {"request_id": "d"}], "total_count": 5},
        3: {"items": [{"request_id": "e"}], "total_count": 5},
    }

    def fake_request_my_generations(access_token: str, page: int = 1) -> dict:
        assert access_token == "jwt"
        calls.append(page)
        return pages[page]

    monkeypatch.setattr(mypage_page, "request_my_generations", fake_request_my_generations)

    generations, total_count = mypage_page._load_generation_pages("jwt")

    assert calls == [1, 2, 3]
    assert total_count == 5
    assert [item["request_id"] for item in generations] == ["a", "b", "c", "d", "e"]


def test_render_recent_work_uses_session_page_and_renders_status(monkeypatch) -> None:
    fake_st = FakeStreamlit({"mypage_page_recent": 2})
    captured: dict[str, object] = {}

    def fake_grid(items: list[dict], folders: list[dict], access_token: str) -> None:
        captured["items"] = items
        captured["folders"] = folders
        captured["access_token"] = access_token

    def fake_pagination(scope: str, current_page: int, total_pages: int) -> None:
        captured["pagination"] = (scope, current_page, total_pages)

    monkeypatch.setattr(views, "st", fake_st)
    monkeypatch.setattr(views, "render_generation_grid", fake_grid)
    monkeypatch.setattr(views, "render_pagination_controls", fake_pagination)

    generations = [{"request_id": f"generation-{index}"} for index in range(12)]
    views.render_recent_work(generations, [{"id": 1, "name": "봄"}], "jwt")

    visible_ids = [item["request_id"] for item in captured["items"]]
    assert visible_ids == ["generation-9", "generation-10", "generation-11"]
    assert captured["folders"] == [{"id": 1, "name": "봄"}]
    assert captured["access_token"] == "jwt"
    assert captured["pagination"] == ("recent", 2, 2)
    assert "총 12개 · 2 / 2" in "".join(fake_st.markdowns)
