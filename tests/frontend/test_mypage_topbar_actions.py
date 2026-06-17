import httpx

from frontend.mypage import download_actions, topbar, work_handoff
from frontend.mypage.selection import SELECTED_GENERATION_IDS_KEY
from frontend.mypage.state import RECENT_VIEW, folder_view


class FakeStreamlit:
    def __init__(self, session_state: dict[str, object] | None = None) -> None:
        self.session_state = session_state or {}
        self.markdowns: list[str] = []
        self.buttons: list[dict[str, object]] = []
        self.links: list[dict[str, object]] = []
        self.downloads: list[dict[str, object]] = []
        self.selects: list[dict[str, object]] = []
        self.errors: list[str] = []
        self.columns_calls: list[tuple[object, str]] = []
        self.rerun_called = False

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append(body)

    def button(self, label: str, **kwargs) -> bool:
        self.buttons.append({"label": label, **kwargs})
        return False

    def link_button(self, label: str, url: str, **kwargs) -> None:
        self.links.append({"label": label, "url": url, **kwargs})

    def download_button(self, label: str, **kwargs) -> None:
        self.downloads.append({"label": label, **kwargs})

    def error(self, message: str) -> None:
        self.errors.append(message)

    def selectbox(self, *args, **kwargs) -> str | None:
        self.selects.append({"args": args, **kwargs})
        options = kwargs.get("options") or (args[1] if len(args) > 1 else [])
        index = int(kwargs.get("index", 0))
        return options[index] if options else None

    def columns(self, spec: object, gap: str) -> list["FakeContext"]:
        self.columns_calls.append((spec, gap))
        count = len(spec) if isinstance(spec, list) else int(spec)
        return [FakeContext() for _ in range(count)]

    def container(self, *, key: str) -> "FakeContext":
        self.markdowns.append(key)
        return FakeContext()

    def rerun(self) -> None:
        self.rerun_called = True


class FakeContext:
    def __enter__(self) -> "FakeContext":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


def _patch_streamlit(monkeypatch, fake_st: FakeStreamlit) -> None:
    monkeypatch.setattr(topbar, "st", fake_st)
    monkeypatch.setattr(download_actions, "st", fake_st)


def test_topbar_enables_original_download_and_folder_for_one_selected_generation(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit({SELECTED_GENERATION_IDS_KEY: ["request-1"]})
    _patch_streamlit(monkeypatch, fake_st)

    def fail_cached_asset_bytes(url: str) -> bytes:
        raise AssertionError(f"single download should link directly, got {url}")

    monkeypatch.setattr(download_actions, "_cached_asset_bytes", fail_cached_asset_bytes)

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[
            {
                "request_id": "request-1",
                "image_url": "/outputs/result.png",
                "download_url": "/api/assets/download/outputs/result.png",
                "original_image_url": "/uploads/source.png",
                "folder_id": None,
            }
        ],
        folders=[{"id": 7, "name": "Spring"}],
    )

    assert [(link["key"], link["url"]) for link in fake_st.links] == [
        ("mypage-action-original", "http://127.0.0.1:8000/uploads/source.png"),
        (
            "mypage-action-download",
            "http://127.0.0.1:8000/api/assets/download/outputs/result.png",
        ),
    ]
    assert fake_st.downloads == []
    assert fake_st.selects[0]["disabled"] is False
    assert any(button["key"] == "mypage-action-folder" for button in fake_st.buttons)
    assert ([0.46, 0.54], "large") in fake_st.columns_calls
    assert ([1, 1, 1, 1, 1.05], "small") in fake_st.columns_calls
    assert any(
        button["key"] == "mypage-action-work-from-image"
        and button["label"] == "↪ 이어작업"
        and button["disabled"] is False
        for button in fake_st.buttons
    )
    folder_button_index = next(
        index
        for index, button in enumerate(fake_st.buttons)
        if button["key"] == "mypage-action-folder"
    )
    assert fake_st.buttons[folder_button_index]["label"] == "⇄ 폴더변경"
    assert fake_st.selects[0]["key"] == "mypage-action-folder-select"
    assert [link["label"] for link in fake_st.links] == ["⌕ 원본보기", "⇩ 다운로드"]


def test_topbar_renders_left_aligned_select_all_action(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    _patch_streamlit(monkeypatch, fake_st)

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[{"request_id": "request-1"}],
        folders=[],
    )

    select_all_button = next(
        button for button in fake_st.buttons if button["key"] == "mypage-action-select-all"
    )
    assert select_all_button["label"] == "전체 선택"
    assert select_all_button["disabled"] is False
    assert select_all_button["use_container_width"] is True


def test_topbar_marks_select_all_action_active_when_current_page_is_selected(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit({SELECTED_GENERATION_IDS_KEY: ["request-1"]})
    _patch_streamlit(monkeypatch, fake_st)

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[{"request_id": "request-1"}],
        folders=[],
    )

    select_all_button = next(
        button for button in fake_st.buttons if button["key"] == "mypage-action-select-all-active"
    )
    assert select_all_button["label"] == "전체 선택"
    assert select_all_button["disabled"] is False


def test_topbar_select_all_toggles_current_page_generations(monkeypatch) -> None:
    fake_st = FakeStreamlit({SELECTED_GENERATION_IDS_KEY: ["hidden-request"]})
    _patch_streamlit(monkeypatch, fake_st)

    def click_select_all(label: str, **kwargs) -> bool:
        fake_st.buttons.append({"label": label, **kwargs})
        return kwargs.get("key") == "mypage-action-select-all"

    fake_st.button = click_select_all

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[{"request_id": "request-1"}, {"request_id": "request-2"}],
        folders=[],
    )

    assert fake_st.session_state[SELECTED_GENERATION_IDS_KEY] == [
        "hidden-request",
        "request-1",
        "request-2",
    ]
    assert fake_st.rerun_called is True


def test_topbar_active_select_all_toggles_current_page_generations_off(monkeypatch) -> None:
    fake_st = FakeStreamlit({SELECTED_GENERATION_IDS_KEY: ["request-1", "request-2"]})
    _patch_streamlit(monkeypatch, fake_st)

    def click_select_all(label: str, **kwargs) -> bool:
        fake_st.buttons.append({"label": label, **kwargs})
        return kwargs.get("key") == "mypage-action-select-all-active"

    fake_st.button = click_select_all

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[{"request_id": "request-1"}, {"request_id": "request-2"}],
        folders=[],
    )

    assert fake_st.session_state[SELECTED_GENERATION_IDS_KEY] == []
    assert fake_st.rerun_called is True


def test_topbar_select_all_uses_visible_folder_page_only(monkeypatch) -> None:
    fake_st = FakeStreamlit({"mypage_page_folder_7": 2})
    _patch_streamlit(monkeypatch, fake_st)

    def click_select_all(label: str, **kwargs) -> bool:
        fake_st.buttons.append({"label": label, **kwargs})
        return kwargs.get("key") == "mypage-action-select-all"

    fake_st.button = click_select_all
    generations = [{"request_id": f"request-{index}", "folder_id": 7} for index in range(13)]

    topbar.render_topbar(
        folder_view(7),
        "Spring",
        "jwt",
        generations=generations,
        folders=[{"id": 7, "name": "Spring"}],
    )

    assert fake_st.session_state[SELECTED_GENERATION_IDS_KEY] == ["request-12"]


def test_topbar_work_from_image_sets_handoff_upload_and_moves_to_work_page(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit(
        {
            SELECTED_GENERATION_IDS_KEY: ["request-1"],
            "result_bytes": b"old",
            "result_copy": {"headline": "old"},
            "result_context": {"prompt": "old"},
        }
    )
    _patch_streamlit(monkeypatch, fake_st)
    navigated_pages: list[str] = []
    monkeypatch.setattr(topbar, "navigate_to", navigated_pages.append)
    monkeypatch.setattr(work_handoff, "request_asset_bytes", lambda url: b"selected-image")

    def click_work_action(label: str, **kwargs) -> bool:
        fake_st.buttons.append({"label": label, **kwargs})
        return kwargs.get("key") == "mypage-action-work-from-image"

    fake_st.button = click_work_action

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[
            {
                "request_id": "request-1",
                "image_url": "/outputs/result.png",
                "preset_id": "instagram",
                "original_image_url": "/uploads/source.png",
                "folder_id": None,
            }
        ],
        folders=[],
    )

    assert fake_st.session_state["work_handoff_upload_bytes"] == b"selected-image"
    assert fake_st.session_state["work_handoff_upload_name"] == "result.png"
    assert fake_st.session_state["work_handoff_upload_type"] == "image/png"
    assert fake_st.session_state["selected_channel"] == "인스타그램"
    assert "result_image_url" not in fake_st.session_state
    assert "result_bytes" not in fake_st.session_state
    assert "result_copy" not in fake_st.session_state
    assert "result_context" not in fake_st.session_state
    assert navigated_pages == ["work"]
    assert fake_st.rerun_called is True


def test_topbar_home_button_navigates_to_main_without_clearing_session(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit({"auth_access_token": "jwt-token"})
    _patch_streamlit(monkeypatch, fake_st)
    navigated_pages: list[str] = []
    monkeypatch.setattr(topbar, "navigate_to", navigated_pages.append)

    def click_home(label: str, **kwargs) -> bool:
        fake_st.buttons.append({"label": label, **kwargs})
        return kwargs.get("key") == "mypage-main-link"

    fake_st.button = click_home

    topbar.render_topbar(
        RECENT_VIEW,
        "?꾩껜 ?묒뾽",
        "jwt",
        generations=[{"request_id": "request-1"}],
        folders=[],
    )

    home_button = next(
        button for button in fake_st.buttons if button.get("key") == "mypage-main-link"
    )
    assert home_button["label"] == topbar.HOME_BUTTON_LABEL
    assert home_button["help"] == topbar.HOME_BUTTON_HELP
    assert navigated_pages == ["main"]
    assert fake_st.session_state["auth_access_token"] == "jwt-token"
    assert fake_st.rerun_called is True
    assert not any('href="?page=main"' in body for body in fake_st.markdowns)


def test_topbar_work_button_navigates_to_work_page_with_icon_button(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit({"auth_access_token": "jwt-token"})
    _patch_streamlit(monkeypatch, fake_st)
    navigated_pages: list[str] = []
    monkeypatch.setattr(topbar, "navigate_to", navigated_pages.append)

    def click_work(label: str, **kwargs) -> bool:
        fake_st.buttons.append({"label": label, **kwargs})
        return kwargs.get("key") == "mypage-work-link"

    fake_st.button = click_work

    topbar.render_topbar(
        RECENT_VIEW,
        "?袁⑷퍥 ?臾믩씜",
        "jwt",
        generations=[{"request_id": "request-1"}],
        folders=[],
    )

    assert not any(
        button.get("key") in {"mypage-new-work", "mypage-new-work-simple"}
        for button in fake_st.buttons
    )
    work_button = next(
        button for button in fake_st.buttons if button.get("key") == "mypage-work-link"
    )
    home_button = next(
        button for button in fake_st.buttons if button.get("key") == "mypage-main-link"
    )
    work_button_index = next(
        index
        for index, button in enumerate(fake_st.buttons)
        if button.get("key") == "mypage-work-link"
    )
    home_button_index = next(
        index
        for index, button in enumerate(fake_st.buttons)
        if button.get("key") == "mypage-main-link"
    )
    assert work_button_index < home_button_index
    assert work_button["label"] == topbar.WORK_BUTTON_LABEL
    assert work_button["help"] == topbar.WORK_BUTTON_HELP
    assert home_button["label"] == topbar.HOME_BUTTON_LABEL
    assert navigated_pages == ["work"]
    assert fake_st.session_state["auth_access_token"] == "jwt-token"
    assert fake_st.rerun_called is True
    assert not any('href="?page=work"' in body for body in fake_st.markdowns)


def test_topbar_single_download_falls_back_to_image_url_when_download_url_is_missing(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit({SELECTED_GENERATION_IDS_KEY: ["request-1"]})
    _patch_streamlit(monkeypatch, fake_st)

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[
            {
                "request_id": "request-1",
                "image_url": "/outputs/result.png",
                "original_image_url": "/uploads/source.png",
                "folder_id": None,
            }
        ],
        folders=[],
    )

    assert {
        "label": "⇩ 다운로드",
        "url": "http://127.0.0.1:8000/outputs/result.png",
        "key": "mypage-action-download",
        "use_container_width": True,
    } in fake_st.links
    assert fake_st.downloads == []


def test_topbar_disables_single_download_when_no_downloadable_url(monkeypatch) -> None:
    fake_st = FakeStreamlit({SELECTED_GENERATION_IDS_KEY: ["request-1"]})
    _patch_streamlit(monkeypatch, fake_st)

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[
            {
                "request_id": "request-1",
                "image_url": None,
                "download_url": None,
                "original_image_url": "/uploads/source.png",
                "folder_id": None,
            }
        ],
        folders=[],
    )

    download_button = next(
        button for button in fake_st.buttons if button["key"] == "mypage-action-download"
    )
    assert download_button["disabled"] is True
    assert fake_st.downloads == []


def test_topbar_allows_zip_download_and_folder_change_for_multiple_selected_generations(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit({SELECTED_GENERATION_IDS_KEY: ["request-1", "request-2"]})
    requested_urls: list[str] = []
    _patch_streamlit(monkeypatch, fake_st)
    monkeypatch.setattr(
        download_actions,
        "_cached_asset_bytes",
        lambda url: requested_urls.append(url) or b"image",
    )

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[
            {
                "request_id": "request-1",
                "image_url": "/outputs/one.png",
                "download_url": "/api/assets/download/outputs/one.png",
                "folder_id": None,
            },
            {
                "request_id": "request-2",
                "image_url": "/outputs/two.png",
                "download_url": "/api/assets/download/outputs/two.png",
                "folder_id": None,
            },
        ],
        folders=[{"id": 7, "name": "Spring"}],
    )

    assert fake_st.links == []
    assert requested_urls == [
        "http://127.0.0.1:8000/api/assets/download/outputs/one.png",
        "http://127.0.0.1:8000/api/assets/download/outputs/two.png",
    ]
    original_button = next(
        button for button in fake_st.buttons if button["key"] == "mypage-action-original"
    )
    work_button = next(
        button for button in fake_st.buttons if button["key"] == "mypage-action-work-from-image"
    )
    folder_button = next(
        button for button in fake_st.buttons if button["key"] == "mypage-action-folder"
    )
    assert work_button["disabled"] is True
    assert original_button["disabled"] is True
    assert folder_button["label"] == "⇄ 폴더변경"
    assert folder_button["disabled"] is False
    assert fake_st.selects[0]["disabled"] is False
    assert fake_st.downloads[0]["key"] == "mypage-action-download"
    assert fake_st.downloads[0]["mime"] == "application/zip"
    assert fake_st.downloads[0]["data"].startswith(b"PK")
    assert fake_st.downloads[0]["disabled"] is False


def test_topbar_suppresses_download_error_message_when_zip_payload_fails(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit({SELECTED_GENERATION_IDS_KEY: ["request-1", "request-2"]})
    _patch_streamlit(monkeypatch, fake_st)

    def fail_asset_download(url: str) -> bytes:
        raise httpx.ConnectError(f"cannot fetch {url}")

    monkeypatch.setattr(download_actions, "_cached_asset_bytes", fail_asset_download)

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[
            {
                "request_id": "request-1",
                "image_url": "/outputs/one.png",
                "download_url": "/api/assets/download/outputs/one.png",
                "folder_id": None,
            },
            {
                "request_id": "request-2",
                "image_url": "/outputs/two.png",
                "download_url": "/api/assets/download/outputs/two.png",
                "folder_id": None,
            },
        ],
        folders=[],
    )

    assert fake_st.errors == []
    assert fake_st.downloads[0]["key"] == "mypage-action-download"
    assert fake_st.downloads[0]["disabled"] is True
    assert fake_st.downloads[0]["data"] == b""


def test_topbar_folder_change_updates_all_selected_generations(monkeypatch) -> None:
    fake_st = FakeStreamlit({SELECTED_GENERATION_IDS_KEY: ["request-1", "request-2"]})
    _patch_streamlit(monkeypatch, fake_st)
    moved: list[tuple[str, str, int | None]] = []
    monkeypatch.setattr(download_actions, "_cached_asset_bytes", lambda url: b"image")

    def click_folder_action(label: str, **kwargs) -> bool:
        fake_st.buttons.append({"label": label, **kwargs})
        return kwargs.get("key") == "mypage-action-folder"

    def choose_spring(*args, **kwargs) -> str:
        fake_st.selects.append({"args": args, **kwargs})
        return "Spring"

    fake_st.button = click_folder_action
    fake_st.selectbox = choose_spring
    monkeypatch.setattr(
        topbar,
        "move_generation_to_folder",
        lambda access_token, request_id, folder_id: moved.append(
            (access_token, request_id, folder_id)
        ),
    )

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[
            {"request_id": "request-1", "image_url": "/outputs/one.png", "folder_id": None},
            {"request_id": "request-2", "image_url": "/outputs/two.png", "folder_id": None},
        ],
        folders=[{"id": 7, "name": "Spring"}],
    )

    assert moved == [("jwt", "request-1", 7), ("jwt", "request-2", 7)]
    assert fake_st.rerun_called is True
