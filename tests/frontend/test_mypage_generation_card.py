from datetime import UTC, datetime, timedelta

from frontend.css.mypage_parts.cards import MYPAGE_CARDS_CSS
from frontend.mypage import generation_card
from frontend.mypage.selection import SELECTED_GENERATION_IDS_KEY


def _created_at_minutes_ago(minutes: int) -> str:
    return (datetime.now(UTC) - timedelta(minutes=minutes)).isoformat()


class FakeStreamlit:
    def __init__(self) -> None:
        self.images: list[str] = []
        self.markdowns: list[str] = []
        self.buttons: list[dict[str, object]] = []
        self.downloads: list[dict[str, object]] = []
        self.links: list[dict[str, object]] = []
        self.selects: list[dict[str, object]] = []
        self.session_state: dict[str, object] = {}
        self.column_counts: list[tuple[object, str]] = []
        self.container_calls: list[dict[str, object]] = []
        self.rerun_called = False

    def image(self, value: str, *, use_container_width: bool = False) -> None:
        self.images.append(value)

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append(body)

    def button(self, label: str, **kwargs) -> bool:
        self.buttons.append({"label": label, **kwargs})
        return False

    def selectbox(self, *args, **kwargs) -> None:
        self.selects.append({"args": args, **kwargs})
        return None

    def download_button(self, *args, **kwargs) -> None:
        self.downloads.append({"args": args, **kwargs})

    def link_button(self, *args, **kwargs) -> None:
        self.links.append({"args": args, **kwargs})

    def columns(self, count: object, gap: str) -> list["FakeContext"]:
        self.column_counts.append((count, gap))
        length = len(count) if isinstance(count, list) else int(count)
        return [FakeContext() for _ in range(length)]

    def container(
        self,
        *,
        border: bool = False,
        height: int | None = None,
        key: str | None = None,
    ) -> "FakeContext":
        self.container_calls.append({"border": border, "height": height, "key": key})
        return FakeContext()

    def rerun(self) -> None:
        self.rerun_called = True


class FakeContext:
    def __enter__(self) -> "FakeContext":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


def test_generation_card_renders_thumbnail_and_selection_toggle_without_inline_actions(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(generation_card, "st", fake_st)

    generation_card._render_generation_card(
        {
            "request_id": "request-1",
            "image_url": "/outputs/result.png",
            "original_image_url": "/uploads/source.png",
            "preset_id": "channel",
            "status": "completed",
            "created_at": "2026-06-10T12:00:00",
        },
        [],
        "jwt",
        selected=False,
    )

    rendered_html = "".join(fake_st.markdowns)
    assert fake_st.images == []
    assert "mypage-image-preview" in rendered_html
    assert "mypage-image-modal" in rendered_html
    assert 'src="http://127.0.0.1:8000/outputs/result.png"' in rendered_html
    assert "mypage-card-select-zone" in rendered_html
    assert fake_st.buttons[0]["label"] == "선택"
    assert fake_st.buttons[0]["key"] == "mypage-select-request-1"
    assert fake_st.buttons[0]["use_container_width"] is True
    assert fake_st.buttons[0]["on_click"] == generation_card.toggle_generation_selection
    assert fake_st.buttons[0]["args"] == (fake_st.session_state, "request-1")
    assert fake_st.column_counts == []
    assert fake_st.links == []
    assert fake_st.downloads == []
    assert fake_st.selects == []


def test_generation_card_toggle_button_uses_on_click_without_manual_rerun(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state[SELECTED_GENERATION_IDS_KEY] = ["request-1"]
    monkeypatch.setattr(generation_card, "st", fake_st)

    def fake_button(label: str, **kwargs) -> bool:
        fake_st.buttons.append({"label": label, **kwargs})
        return False

    fake_st.button = fake_button

    generation_card._render_generation_card(
        {
            "request_id": "request-1",
            "image_url": "/outputs/result.png",
            "preset_id": "channel",
            "status": "success",
            "created_at": "2026-06-10T12:00:00",
        },
        [],
        "jwt",
        selected=True,
    )

    button = fake_st.buttons[0]
    assert button["key"] == "mypage-select-request-1"
    assert button["on_click"] == generation_card.toggle_generation_selection
    assert button["args"] == (fake_st.session_state, "request-1")
    assert not fake_st.rerun_called

    button["on_click"](*button["args"])
    assert fake_st.session_state[SELECTED_GENERATION_IDS_KEY] == []
    assert fake_st.buttons[0]["label"] == "선택 해제"


def test_generation_card_keeps_meta_on_one_line_and_removes_per_card_controls(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(generation_card, "st", fake_st)

    generation_card._render_generation_card(
        {
            "request_id": "failed-request",
            "image_url": None,
            "original_image_url": "/uploads/source.png",
            "preset_id": "daangn",
            "folder_id": 7,
            "status": "failed",
            "created_at": "2026-06-10T12:00:00",
        },
        [{"id": 7, "name": "봄 신메뉴"}],
        "jwt",
        selected=False,
    )

    rendered_html = "".join(fake_st.markdowns)
    assert '<span class="mypage-card-identity">daangn 2026.06.10</span>' in rendered_html
    assert '<span class="mypage-card-folder">폴더: 봄 신메뉴</span>' in rendered_html
    assert "failed" not in rendered_html
    assert "mypage-card-date" not in rendered_html
    assert fake_st.downloads == []
    assert fake_st.links == []
    assert fake_st.selects == []


def test_generation_card_shows_loading_state_for_pending_image(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(generation_card, "st", fake_st)

    generation_card._render_generation_card(
        {
            "request_id": "pending-request",
            "image_url": None,
            "original_image_url": "/uploads/source.png",
            "preset_id": "instagram",
            "status": "pending",
            "created_at": _created_at_minutes_ago(1),
        },
        [],
        "jwt",
        selected=False,
    )

    rendered_html = "".join(fake_st.markdowns)
    assert "mypage-generating-thumb" in rendered_html
    assert "mypage-generating-spinner" in rendered_html
    assert "mypage-empty-thumb" not in rendered_html
    assert fake_st.downloads == []


def test_generation_card_marks_old_pending_image_as_timed_out(
    monkeypatch,
) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(generation_card, "st", fake_st)

    generation_card._render_generation_card(
        {
            "request_id": "old-pending-request",
            "image_url": None,
            "original_image_url": "/uploads/source.png",
            "preset_id": "instagram",
            "status": "pending",
            "created_at": _created_at_minutes_ago(10),
        },
        [],
        "jwt",
        selected=False,
    )

    rendered_html = "".join(fake_st.markdowns)
    assert "mypage-stale-thumb" in rendered_html
    assert "mypage-generating-thumb" not in rendered_html
    assert "폴더: 미분류" in rendered_html
    assert "timeout" not in rendered_html
    assert fake_st.downloads == []


def test_generation_waiting_helper_tracks_only_fresh_pending_without_image() -> None:
    assert generation_card.has_generation_waiting_for_image(
        [
            {
                "image_url": None,
                "status": "pending",
                "created_at": _created_at_minutes_ago(1),
            }
        ]
    )
    assert not generation_card.has_generation_waiting_for_image(
        [
            {
                "image_url": "/outputs/result.png",
                "status": "pending",
                "created_at": _created_at_minutes_ago(1),
            }
        ]
    )
    assert not generation_card.has_generation_waiting_for_image(
        [
            {
                "image_url": None,
                "status": "pending",
                "created_at": _created_at_minutes_ago(10),
            }
        ]
    )
    assert not generation_card.has_generation_waiting_for_image(
        [
            {
                "image_url": None,
                "status": "success",
                "created_at": _created_at_minutes_ago(1),
            }
        ]
    )


def test_generation_grid_uses_four_equal_columns(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    rendered_items: list[tuple[str, bool]] = []
    monkeypatch.setattr(generation_card, "st", fake_st)
    monkeypatch.setattr(
        generation_card,
        "_render_generation_card",
        lambda item, folders, access_token, selected=False: rendered_items.append(
            (item["request_id"], selected)
        ),
    )

    generation_card.render_generation_grid(
        [{"request_id": f"request-{index}"} for index in range(5)],
        [],
        "jwt",
    )

    assert fake_st.column_counts == [(4, "medium")]
    assert fake_st.container_calls == [
        {"border": True, "height": 330, "key": f"mypage-generation-card-request-{index}"}
        for index in range(5)
    ]
    assert rendered_items == [(f"request-{index}", False) for index in range(5)]


def test_generation_grid_marks_selected_card_container(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    fake_st.session_state[SELECTED_GENERATION_IDS_KEY] = ["request-1"]
    rendered_items: list[tuple[str, bool]] = []
    monkeypatch.setattr(generation_card, "st", fake_st)
    monkeypatch.setattr(
        generation_card,
        "_render_generation_card",
        lambda item, folders, access_token, selected=False: rendered_items.append(
            (item["request_id"], selected)
        ),
    )

    generation_card.render_generation_grid(
        [{"request_id": f"request-{index}"} for index in range(3)],
        [],
        "jwt",
    )

    assert fake_st.container_calls == [
        {"border": True, "height": 330, "key": "mypage-generation-card-request-0"},
        {
            "border": True,
            "height": 330,
            "key": "mypage-generation-card-selected-request-1",
        },
        {"border": True, "height": 330, "key": "mypage-generation-card-request-2"},
    ]
    assert rendered_items == [
        ("request-0", False),
        ("request-1", True),
        ("request-2", False),
    ]


def test_generation_card_css_keeps_cards_and_images_uniform() -> None:
    source = MYPAGE_CARDS_CSS

    assert "height: 330px" in source
    assert "border-color: transparent !important" in source
    assert "--mypage-generation-thumb-height: 241px" in source
    assert "height: var(--mypage-generation-thumb-height)" in source
    assert "object-fit: contain" in source
    assert ".mypage-image-modal" in source
    assert "position: fixed" in source
    assert "max-height: calc(100vh - 96px)" in source
    assert "cursor: zoom-in" in source
    assert "overflow: hidden" in source
    assert ".mypage-generating-thumb" in source
    assert ".mypage-generating-spinner" in source
    assert ".mypage-stale-thumb" in source


def test_generation_card_meta_stays_inside_fixed_card_width() -> None:
    source = MYPAGE_CARDS_CSS

    assert ".mypage-card-meta" in source
    assert "grid-template-columns" in source
    assert "mypage-card-identity" in source
    assert "mypage-card-folder" in source
    assert "min-width: 0" in source
    assert "box-sizing: border-box" in source
    assert "text-align: right" in source
    assert "max-width: 100%" in source


def test_generation_card_controls_share_thumbnail_width() -> None:
    source = MYPAGE_CARDS_CSS

    assert "--mypage-generation-content-width: 267px" in source
    assert '[class*="st-key-mypage-generation-card-"]' in source
    assert "width: min(100%, var(--mypage-generation-content-width))" in source
    assert ".mypage-image-preview" in source
    assert ".mypage-card-meta" in source
    assert ".mypage-card-select-zone" in source
    assert '[class*="st-key-mypage-select-"] button' in source
    assert "margin-left: auto" in source
    assert "margin-right: auto" in source


def test_generation_card_css_does_not_wait_for_inner_marker() -> None:
    source = MYPAGE_CARDS_CSS

    assert "mypage-generation-card-marker" not in source
    assert ":has(.mypage-generation-card-marker)" not in source


def test_generation_card_selection_and_toolbar_actions_have_distinct_styles() -> None:
    source = MYPAGE_CARDS_CSS

    assert '[class*="st-key-mypage-generation-card-selected-"]' in source
    assert "border-width: 3px !important" in source
    assert "border-color: #00a6a6 !important" in source
    assert '[class*="st-key-mypage-action-select-all"] button' in source
    assert "width: min(100%, calc(267px * 0.6))" in source
    assert '[class*="st-key-mypage-action-select-all-active"] button' in source
    assert '[class*="st-key-mypage-action-work-from-image"] button' in source
    assert '[class*="st-key-mypage-action-original"] a' in source
    assert '[class*="st-key-mypage-action-download"] a' in source
    assert '[class*="st-key-mypage-action-download"] button' in source
    assert '[class*="st-key-mypage-action-folder"] button' in source
    assert 'div[data-testid="stLinkButton"] a' in source
    assert 'div[data-testid="stDownloadButton"] button' in source
    assert "height: 53px !important" in source
    assert "min-height: 53px !important" in source
    assert "width: 100% !important" in source
    assert "min-width: 0 !important" in source
    assert "font-size: 16.25px !important" in source
    assert "white-space: nowrap !important" in source
    assert "#5a463c" in source
    assert "#34383d" in source
    assert "#53613b" in source
    assert "#39467a" in source
    assert "border: 0 !important" in source
    assert "color: #ffffff !important" in source
    assert "-webkit-text-fill-color: #ffffff !important" in source
    assert "box-sizing: border-box !important" in source
    assert "background: #fbfaf6 !important" in source
    assert "background: #f2f5f3 !important" in source
    assert "-webkit-text-fill-color: #00a6a6 !important" in source
    assert "-webkit-text-fill-color: #9aa4a0 !important" in source
    assert "button:disabled" in source
