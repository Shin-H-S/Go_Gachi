from frontend.mypage import views
from frontend.mypage.pagination import page_count, page_status_text, paginate_items
from frontend.pages import mypage as mypage_page


class FakeStreamlit:
    def __init__(self, session_state: dict[str, object] | None = None) -> None:
        self.session_state = session_state or {}
        self.markdowns: list[str] = []
        self.images: list[str] = []
        self.column_counts: list[tuple[int, str]] = []

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        assert unsafe_allow_html is True
        self.markdowns.append(body)

    def image(self, value: str, *, use_container_width: bool = False) -> None:
        self.images.append(value)

    def columns(self, count: int, gap: str) -> list["FakeContext"]:
        self.column_counts.append((count, gap))
        return [FakeContext() for _ in range(count)]

    def container(self, *, border: bool = False) -> "FakeContext":
        return FakeContext()


class FakeContext:
    def __enter__(self) -> "FakeContext":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


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


def test_load_recent_generation_page_fetches_only_intersecting_backend_pages(monkeypatch) -> None:
    # 페이지당 12개로 동일하므로 프론트 페이지 N은 백엔드 페이지 N과 1:1 매칭된다.
    calls: list[int] = []
    pages = {
        2: {
            "items": [{"request_id": f"generation-{index}"} for index in range(12, 24)],
            "total_count": 25,
        },
    }

    def fake_request_my_generations(access_token: str, page: int = 1) -> dict:
        assert access_token == "jwt"
        calls.append(page)
        return pages[page]

    monkeypatch.setattr(mypage_page, "request_my_generations", fake_request_my_generations)

    generations, total_count, current_page = mypage_page._load_recent_generation_page(
        "jwt",
        page=2,
    )

    assert calls == [2]
    assert total_count == 25
    assert current_page == 2
    assert [item["request_id"] for item in generations] == [
        f"generation-{index}" for index in range(12, 24)
    ]


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

    generations = [{"request_id": f"generation-{index}"} for index in range(12, 24)]
    views.render_recent_work(
        generations,
        [{"id": 1, "name": "봄"}],
        "jwt",
        total_count=25,
        current_page=2,
    )

    visible_ids = [item["request_id"] for item in captured["items"]]
    assert visible_ids == [f"generation-{index}" for index in range(12, 24)]
    assert captured["folders"] == [{"id": 1, "name": "봄"}]
    assert captured["access_token"] == "jwt"
    assert captured["pagination"] == ("recent", 2, 3)
    assert "총 25개 · 2 / 3" in "".join(fake_st.markdowns)


def test_render_uploads_uses_date_in_meta_without_original_photo_label(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(views, "st", fake_st)

    views.render_uploads(
        [
            {
                "original_image_url": "https://backend.example/uploads/menu.png",
                "created_at": "2026-06-10T12:00:00",
                "used_count": 2,
            }
        ]
    )

    rendered_html = "".join(fake_st.markdowns)
    assert "<span>2026.06.10</span>" in rendered_html
    assert "원본 사진" not in rendered_html
    assert "mypage-card-date" not in rendered_html
