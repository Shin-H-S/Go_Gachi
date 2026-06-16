from datetime import UTC, datetime, timedelta

from frontend.mypage import state, views
from frontend.pages import mypage as mypage_page


def _created_at_minutes_ago(minutes: int) -> str:
    return (datetime.now(UTC) - timedelta(minutes=minutes)).isoformat()


class FakeStreamlit:
    def __init__(self, session_state: dict[str, object] | None = None) -> None:
        self.session_state = session_state or {}
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.buttons: list[str] = []
        self.columns_calls: list[tuple[object, str]] = []
        self.container_keys: list[str | None] = []
        self.rerun_called = False

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def button(self, label: str, **kwargs) -> bool:
        self.buttons.append(label)
        return False

    def rerun(self) -> None:
        self.rerun_called = True

    def container(self, *, key: str | None = None, **kwargs) -> "FakeContext":
        self.container_keys.append(key)
        return FakeContext()

    def columns(self, spec: object, gap: str) -> list["FakeContext"]:
        self.columns_calls.append((spec, gap))
        count = len(spec) if isinstance(spec, list) else int(spec)
        return [FakeContext() for _ in range(count)]


class FakeContext:
    def __enter__(self) -> "FakeContext":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


def _patch_common_profile_requests(monkeypatch) -> None:
    monkeypatch.setattr(
        mypage_page,
        "request_me",
        lambda access_token: {"email": f"{access_token}@example.com"},
    )
    monkeypatch.setattr(
        mypage_page,
        "request_my_folders",
        lambda access_token: {"items": [{"id": 7, "name": "Spring"}]},
    )


def test_load_mypage_data_recent_fetches_only_server_pages_needed(monkeypatch) -> None:
    _patch_common_profile_requests(monkeypatch)
    monkeypatch.setattr(views, "current_page", lambda scope: 2)
    monkeypatch.setattr(
        mypage_page,
        "request_my_uploads",
        lambda access_token: (_ for _ in ()).throw(AssertionError("uploads not expected")),
    )
    # 페이지당 12개로 정렬되어 프론트 페이지 N은 백엔드 페이지 N 한 번만 요청한다.
    calls: list[int] = []
    backend_pages = {
        2: {
            "items": [{"request_id": f"generation-{index}"} for index in range(12, 24)],
            "total_count": 25,
        },
    }

    def fake_generations(access_token: str, page: int = 1) -> dict:
        assert access_token == "jwt"
        calls.append(page)
        return backend_pages[page]

    monkeypatch.setattr(mypage_page, "request_my_generations", fake_generations)

    profile, folders, generations, uploads, total_count, current_page = (
        mypage_page._load_mypage_data("jwt", state.RECENT_VIEW)
    )

    assert profile == {"email": "jwt@example.com"}
    assert folders == [{"id": 7, "name": "Spring"}]
    assert calls == [2]
    assert [item["request_id"] for item in generations] == [
        f"generation-{index}" for index in range(12, 24)
    ]
    assert uploads == []
    assert total_count == 25
    assert current_page == 2


def test_load_mypage_data_folder_view_keeps_full_load_for_folder_filtering(monkeypatch) -> None:
    _patch_common_profile_requests(monkeypatch)
    monkeypatch.setattr(
        mypage_page,
        "request_my_uploads",
        lambda access_token: (_ for _ in ()).throw(AssertionError("uploads not expected")),
    )
    calls: list[int] = []
    backend_pages = {
        1: {"items": [{"request_id": "a"}, {"request_id": "b"}], "total_count": 3},
        2: {"items": [{"request_id": "c"}], "total_count": 3},
    }

    def fake_generations(access_token: str, page: int = 1) -> dict:
        assert access_token == "jwt"
        calls.append(page)
        return backend_pages[page]

    monkeypatch.setattr(mypage_page, "request_my_generations", fake_generations)

    _, _, generations, uploads, total_count, current_page = mypage_page._load_mypage_data(
        "jwt",
        state.folder_view(7),
    )

    assert calls == [1, 2]
    assert [item["request_id"] for item in generations] == ["a", "b", "c"]
    assert uploads == []
    assert total_count == 3
    assert current_page == 1


def test_load_mypage_data_uploads_and_account_views_skip_generation_fetches(monkeypatch) -> None:
    _patch_common_profile_requests(monkeypatch)
    monkeypatch.setattr(
        mypage_page,
        "request_my_generations",
        lambda access_token, page=1: (_ for _ in ()).throw(
            AssertionError("generations not expected")
        ),
    )
    monkeypatch.setattr(
        mypage_page,
        "request_my_uploads",
        lambda access_token: {"items": [{"id": "upload-1"}]},
    )

    _, _, generations, uploads, total_count, current_page = mypage_page._load_mypage_data(
        "jwt",
        state.UPLOADS_VIEW,
    )

    assert generations == []
    assert uploads == [{"id": "upload-1"}]
    assert total_count == 0
    assert current_page == 1

    monkeypatch.setattr(
        mypage_page,
        "request_my_uploads",
        lambda access_token: (_ for _ in ()).throw(AssertionError("uploads not expected")),
    )

    _, _, generations, uploads, total_count, current_page = mypage_page._load_mypage_data(
        "jwt",
        state.ACCOUNT_VIEW,
    )

    assert generations == []
    assert uploads == []
    assert total_count == 0
    assert current_page == 1


def test_render_mypage_page_normalizes_legacy_all_view_to_recent(monkeypatch) -> None:
    fake_st = FakeStreamlit(
        {
            "auth_access_token": "jwt",
            "mypage_view": state.FOLDER_ALL_VIEW,
        }
    )
    calls: dict[str, object] = {}

    def fake_load(
        access_token: str, view: str
    ) -> tuple[dict, list[dict], list[dict], list[dict], int, int]:
        calls["load"] = (access_token, view)
        return {"email": "owner@example.com"}, [{"id": 1, "name": "Spring"}], [{"id": 1}], [], 12, 1

    monkeypatch.setattr(mypage_page, "st", fake_st)
    monkeypatch.setattr(mypage_page, "_load_mypage_data", fake_load)
    monkeypatch.setattr(
        mypage_page,
        "render_sidebar",
        lambda profile, folders, view, access_token: calls.setdefault(
            "sidebar", (profile, folders, view, access_token)
        ),
    )
    monkeypatch.setattr(
        mypage_page,
        "render_topbar",
        lambda view, title, access_token, **kwargs: calls.setdefault(
            "topbar", (view, title, access_token, kwargs)
        ),
    )
    monkeypatch.setattr(
        mypage_page,
        "render_recent_work",
        lambda generations, folders, access_token, **kwargs: calls.setdefault(
            "recent", (generations, folders, access_token, kwargs)
        ),
    )
    monkeypatch.setattr(
        mypage_page,
        "render_uploads",
        lambda uploads: (_ for _ in ()).throw(AssertionError("uploads view not expected")),
    )
    monkeypatch.setattr(
        mypage_page,
        "render_account_settings",
        lambda profile: (_ for _ in ()).throw(AssertionError("account view not expected")),
    )
    monkeypatch.setattr(
        mypage_page,
        "render_folder_view",
        lambda view, generations, folders, access_token: (_ for _ in ()).throw(
            AssertionError("folder view not expected")
        ),
    )

    mypage_page.render_mypage_page()

    assert fake_st.session_state["mypage_view"] == state.RECENT_VIEW
    assert calls["load"] == ("jwt", state.RECENT_VIEW)
    assert calls["sidebar"][2] == state.RECENT_VIEW
    assert calls["topbar"][0] == state.RECENT_VIEW
    assert calls["topbar"][3] == {
        "generations": [{"id": 1}],
        "folders": [{"id": 1, "name": "Spring"}],
    }
    assert calls["recent"][3] == {"total_count": 12, "current_page": 1}
    assert fake_st.container_keys == ["mypage-shell"]


def test_pending_generation_auto_refresh_runs_only_for_fresh_pending(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    refresh_calls: list[str] = []
    monkeypatch.setattr(mypage_page, "st", fake_st)
    monkeypatch.setattr(
        mypage_page,
        "_pending_generation_auto_refresh",
        lambda: refresh_calls.append("refresh"),
    )

    mypage_page._maybe_render_pending_generation_auto_refresh(
        [
            {
                "image_url": None,
                "status": "pending",
                "created_at": _created_at_minutes_ago(1),
            }
        ]
    )

    assert refresh_calls == ["refresh"]

    refresh_calls.clear()
    fake_st.session_state[mypage_page.PENDING_REFRESH_SESSION_KEY] = 123.0

    mypage_page._maybe_render_pending_generation_auto_refresh(
        [
            {
                "image_url": None,
                "status": "pending",
                "created_at": _created_at_minutes_ago(10),
            }
        ]
    )

    assert refresh_calls == []
    assert mypage_page.PENDING_REFRESH_SESSION_KEY not in fake_st.session_state
