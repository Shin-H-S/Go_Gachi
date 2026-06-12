from pathlib import Path

from frontend.mypage import generation_card

ROOT_DIR = Path(__file__).resolve().parents[2]
MYPAGE_CARD_CSS = ROOT_DIR / "frontend" / "css" / "mypage_parts" / "cards.py"


class FakeStreamlit:
    def __init__(self) -> None:
        self.images: list[str] = []
        self.markdowns: list[str] = []
        self.downloads: list[dict[str, object]] = []
        self.links: list[dict[str, object]] = []
        self.session_state: dict[str, object] = {}
        self.column_counts: list[tuple[int, str]] = []
        self.container_calls: list[dict[str, object]] = []

    def image(self, value: str, *, use_container_width: bool = False) -> None:
        self.images.append(value)

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append(body)

    def selectbox(self, *args, **kwargs) -> None:
        return None

    def download_button(self, *args, **kwargs) -> None:
        self.downloads.append({"args": args, **kwargs})

    def link_button(self, *args, **kwargs) -> None:
        self.links.append({"args": args, **kwargs})

    def columns(self, count: int, gap: str) -> list["FakeContext"]:
        self.column_counts.append((count, gap))
        return [FakeContext() for _ in range(count)]

    def container(
        self,
        *,
        border: bool = False,
        height: int | None = None,
        key: str | None = None,
    ) -> "FakeContext":
        self.container_calls.append({"border": border, "height": height, "key": key})
        return FakeContext()


class FakeContext:
    def __enter__(self) -> "FakeContext":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None


def test_generation_card_renders_original_image_as_new_tab_link(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(generation_card, "st", fake_st)
    monkeypatch.setattr(generation_card, "_cached_asset_bytes", lambda url: b"image")

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
    )

    assert len(fake_st.images) == 1
    assert fake_st.images[0].endswith("/outputs/result.png")
    rendered_html = "".join(fake_st.markdowns)
    assert fake_st.column_counts == [(2, "small")]
    assert fake_st.links == [
        {
            "args": ("원본", "http://127.0.0.1:8000/uploads/source.png"),
            "key": "mypage-original-request-1",
            "use_container_width": True,
        }
    ]
    assert fake_st.downloads[0]["args"] == ("다운로드",)
    assert fake_st.downloads[0]["key"] == "mypage-download-request-1"
    assert fake_st.downloads[0]["use_container_width"] is True
    assert "원본: source.png" not in rendered_html


def test_generation_card_keeps_meta_on_one_line_and_disables_missing_download(
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
            "status": "failed",
            "created_at": "2026-06-10T12:00:00",
        },
        [],
        "jwt",
    )

    rendered_html = "".join(fake_st.markdowns)
    assert "<span>daangn</span>" in rendered_html
    assert "<span>2026.06.10: failed</span>" in rendered_html
    assert "mypage-card-date" not in rendered_html
    assert fake_st.downloads[0]["args"] == ("다운로드",)
    assert fake_st.downloads[0]["disabled"] is True
    assert fake_st.downloads[0]["data"] == b""


def test_generation_grid_uses_four_equal_columns(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    rendered_items: list[str] = []
    monkeypatch.setattr(generation_card, "st", fake_st)
    monkeypatch.setattr(
        generation_card,
        "_render_generation_card",
        lambda item, folders, access_token: rendered_items.append(item["request_id"]),
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
    assert rendered_items == [f"request-{index}" for index in range(5)]


def test_generation_card_css_keeps_cards_and_images_uniform() -> None:
    source = MYPAGE_CARD_CSS.read_text(encoding="utf-8")

    assert "height: 330px" in source
    assert "height: 150px" in source
    assert "object-fit: contain" in source
    assert "overflow: hidden" in source


def test_generation_card_meta_stays_inside_fixed_card_width() -> None:
    source = MYPAGE_CARD_CSS.read_text(encoding="utf-8")

    assert ".mypage-card-meta" in source
    assert "grid-template-columns" in source
    assert "min-width: 0" in source
    assert "box-sizing: border-box" in source
    assert "text-align: right" in source
    assert "max-width: 100%" in source


def test_generation_card_controls_share_thumbnail_width() -> None:
    source = MYPAGE_CARD_CSS.read_text(encoding="utf-8")

    assert "--mypage-generation-content-width: 267px" in source
    assert '[class*="st-key-mypage-generation-card-"]' in source
    assert "width: min(100%, var(--mypage-generation-content-width))" in source
    assert 'div[data-testid="stImage"]' in source
    assert ".mypage-card-meta" in source
    assert 'div[data-testid="stSelectbox"]' in source
    assert 'div[data-testid="stHorizontalBlock"]' in source
    assert "margin-left: auto" in source
    assert "margin-right: auto" in source


def test_generation_card_css_does_not_wait_for_inner_marker() -> None:
    source = MYPAGE_CARD_CSS.read_text(encoding="utf-8")

    assert "mypage-generation-card-marker" not in source
    assert ":has(.mypage-generation-card-marker)" not in source


def test_generation_card_action_buttons_have_matching_size_and_distinct_colors() -> None:
    source = MYPAGE_CARD_CSS.read_text(encoding="utf-8")

    assert '[class*="st-key-mypage-original-"] a' in source
    assert '[class*="st-key-mypage-original-"] button' in source
    assert '[class*="st-key-mypage-download-"] button' in source
    assert 'div[data-testid="stLinkButton"] a' in source
    assert 'div[data-testid="stDownloadButton"] button' in source
    assert "height: 34px !important" in source
    assert "min-height: 34px !important" in source
    assert "box-sizing: border-box !important" in source
    assert "background: #f5f4ee !important" in source
    assert "background: #eaf4ff !important" in source
    assert "-webkit-text-fill-color: #245c8f !important" in source
    assert "button:disabled" in source
