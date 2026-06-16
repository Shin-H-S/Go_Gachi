from base64 import b64decode

from frontend.work import loading_panel, result_panel
from frontend.work.loading_icons import loading_icon_data_url
from frontend.work.loading_panel import (
    LOADING_BACKGROUNDS,
    LOADING_ICON_FILES,
    LOADING_TIP_INTERVAL_SECONDS,
    LOADING_TIPS,
    loading_panel_html,
)


def _first_loading_card(html: str) -> str:
    return html.split('class="loading-tip-card"', 1)[1].split("</article>", 1)[0]


def test_loading_panel_uses_curated_tips_without_cliche_label() -> None:
    html = loading_panel_html()

    assert LOADING_TIP_INTERVAL_SECONDS == 7
    assert len(LOADING_TIPS) == 17
    assert html.count('class="loading-tip-card"') == 17
    assert "꿀팁" not in html
    assert "촬영 팁" not in html
    assert "상품 팁" not in html
    assert "구도 팁" not in html
    assert "요청 팁" not in html
    assert "문구 팁" not in html
    assert "활용 팁" not in html
    assert "광고할 상품에 초점을 맞춰 촬영해 주세요" in html
    assert "마이페이지에서 여러 이미지를 ZIP으로 받을 수 있어요" in html
    assert 'class="loading-clay-icon"' in html
    assert 'src="data:image/png;base64,' in html
    assert 'class="loading-tip-heading"' in html
    assert 'class="loading-tip-icon"' not in html
    assert 'class="loading-tip-kicker"' not in html
    assert html.index('class="loading-clay-icon"') < html.index("<strong>")
    assert 'class="loading-progress-dots"' in html
    assert "이미지를 다듬는 중이에요" in html


def test_loading_panel_uses_seventeen_clay_icons() -> None:
    assert len(LOADING_ICON_FILES) == len(LOADING_TIPS)
    assert LOADING_ICON_FILES[0] == "1_mango_passionfruit_ade.png"
    assert LOADING_ICON_FILES[-1] == "17_fat_macaron.png"


def test_loading_icon_assets_resolve_to_png_data_urls() -> None:
    for filename in LOADING_ICON_FILES:
        data_url = loading_icon_data_url(filename)
        payload = data_url.split(",", 1)[1]

        assert data_url.startswith("data:image/png;base64,")
        assert b64decode(payload).startswith(b"\x89PNG\r\n\x1a\n")


def test_loading_panel_uses_twelve_pastel_backgrounds() -> None:
    assert len(LOADING_BACKGROUNDS) == 12


def test_loading_panel_rotates_sequence_from_start_index() -> None:
    html = loading_panel_html(start_index=3)
    first_card = _first_loading_card(html)

    assert 'style="--tip-index: 0;' in first_card
    assert f"--tip-bg: {LOADING_BACKGROUNDS[3]}" in first_card
    assert str(LOADING_TIPS[3]["title"]) in first_card
    assert html.index(str(LOADING_TIPS[3]["title"])) < html.index(str(LOADING_TIPS[4]["title"]))


def test_loading_panel_wraps_start_index_and_pairs_matching_icon(monkeypatch) -> None:
    monkeypatch.setattr(
        loading_panel,
        "loading_icon_data_url",
        lambda filename: f"icon://{filename}",
    )

    html = loading_panel_html(start_index=len(LOADING_TIPS) + 2)
    first_card = _first_loading_card(html)

    assert str(LOADING_TIPS[2]["title"]) in first_card
    assert f'src="icon://{LOADING_ICON_FILES[2]}"' in first_card


def test_loading_panel_random_start_does_not_repeat_previous(monkeypatch) -> None:
    monkeypatch.setattr(loading_panel, "_LAST_LOADING_START_INDEX", 4)
    monkeypatch.setattr(loading_panel, "randrange", lambda _: 4)

    assert loading_panel._next_loading_start_index() == 5


def test_loading_tip_copy_omits_terminal_periods() -> None:
    for tip in LOADING_TIPS:
        assert str(tip["title"])[-1] != "."
        assert str(tip["body"])[-1] != "."


def test_loading_tip_titles_stay_under_long_line_limit() -> None:
    long_line_limit = len("반사, 그림자, 포장 비닐이 상품을 가리지 않게 촬영해주세요")

    for tip in LOADING_TIPS:
        assert len(str(tip["title"])) < long_line_limit
        assert len(str(tip["body"])) < long_line_limit


def test_result_panel_shows_loading_panel_only_while_generating(monkeypatch) -> None:
    calls: list[tuple[str, str | None, str]] = []

    def fake_render_preview_shell(
        format_label: str,
        body_html: str,
        detail_label: str | None = None,
        summary_html: str = "",
    ) -> None:
        calls.append((format_label, detail_label, body_html))

    monkeypatch.setattr(result_panel, "render_preview_shell", fake_render_preview_shell)
    monkeypatch.setattr(result_panel, "loading_panel_html", lambda: "<loading-panel>")
    monkeypatch.setattr(
        result_panel,
        "_render_preview_history_controls",
        lambda **_: calls.append(("history", None, "")),
    )

    result_panel.render_result_panel(
        is_generating=True,
        uploaded_file=None,
        format_label="인스타그램",
        detail_label="스토리 이미지",
    )

    assert calls == [
        (
            "인스타그램",
            "스토리 이미지",
            "<loading-panel>",
        )
    ]
