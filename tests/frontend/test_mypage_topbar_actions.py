from frontend.mypage import topbar
from frontend.mypage.selection import SELECTED_GENERATION_IDS_KEY
from frontend.mypage.state import RECENT_VIEW


class FakeStreamlit:
    def __init__(self, session_state: dict[str, object] | None = None) -> None:
        self.session_state = session_state or {}
        self.markdowns: list[str] = []
        self.buttons: list[dict[str, object]] = []
        self.links: list[dict[str, object]] = []
        self.downloads: list[dict[str, object]] = []
        self.selects: list[dict[str, object]] = []
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

    def selectbox(self, *args, **kwargs) -> str | None:
        self.selects.append({"args": args, **kwargs})
        options = kwargs.get("options") or (args[1] if len(args) > 1 else [])
        index = int(kwargs.get("index", 0))
        return options[index] if options else None

    def columns(self, spec: object, gap: str) -> list["FakeContext"]:
        self.columns_calls.append((spec, gap))
        count = len(spec) if isinstance(spec, list) else int(spec)
        return [FakeContext() for _ in range(count)]

    def rerun(self) -> None:
        self.rerun_called = True


class FakeContext:
    def __enter__(self) -> "FakeContext":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


def test_topbar_enables_original_download_and_folder_for_one_selected_generation(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit({SELECTED_GENERATION_IDS_KEY: ["request-1"]})
    monkeypatch.setattr(topbar, "st", fake_st)
    monkeypatch.setattr(topbar, "_cached_asset_bytes", lambda url: b"image")

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
        folders=[{"id": 7, "name": "Spring"}],
    )

    assert fake_st.links == [
        {
            "label": "원본 보기",
            "url": "http://127.0.0.1:8000/uploads/source.png",
            "key": "mypage-action-original",
            "use_container_width": True,
        }
    ]
    assert fake_st.downloads[0]["key"] == "mypage-action-download"
    assert fake_st.downloads[0]["data"] == b"image"
    assert fake_st.downloads[0]["disabled"] is False
    assert fake_st.selects[0]["disabled"] is False
    assert any(button["key"] == "mypage-action-folder" for button in fake_st.buttons)
    assert ([1, 1, 1, 1.05], "small") in fake_st.columns_calls
    folder_button_index = next(
        index
        for index, button in enumerate(fake_st.buttons)
        if button["key"] == "mypage-action-folder"
    )
    assert fake_st.buttons[folder_button_index]["label"] == "폴더 설정"
    assert fake_st.selects[0]["key"] == "mypage-action-folder-select"


def test_topbar_allows_only_zip_download_for_multiple_selected_generations(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit({SELECTED_GENERATION_IDS_KEY: ["request-1", "request-2"]})
    monkeypatch.setattr(topbar, "st", fake_st)
    monkeypatch.setattr(topbar, "_cached_asset_bytes", lambda url: b"image")

    topbar.render_topbar(
        RECENT_VIEW,
        "전체 작업",
        "jwt",
        generations=[
            {"request_id": "request-1", "image_url": "/outputs/one.png"},
            {"request_id": "request-2", "image_url": "/outputs/two.png"},
        ],
        folders=[],
    )

    assert fake_st.links == []
    original_button = next(
        button for button in fake_st.buttons if button["key"] == "mypage-action-original"
    )
    folder_button = next(
        button for button in fake_st.buttons if button["key"] == "mypage-action-folder"
    )
    assert original_button["disabled"] is True
    assert folder_button["disabled"] is True
    assert fake_st.selects[0]["disabled"] is True
    assert fake_st.downloads[0]["key"] == "mypage-action-download"
    assert fake_st.downloads[0]["mime"] == "application/zip"
    assert fake_st.downloads[0]["data"].startswith(b"PK")
    assert fake_st.downloads[0]["disabled"] is False
