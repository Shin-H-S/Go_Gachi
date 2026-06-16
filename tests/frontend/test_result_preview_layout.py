import inspect

from frontend.work import result_copy, result_panel


class FakeStreamlit:
    def __init__(self, session_state: dict[str, object] | None = None) -> None:
        self.session_state = session_state or {}
        self.markdowns: list[str] = []

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        assert unsafe_allow_html is True
        self.markdowns.append(body)


def test_result_panel_embeds_summary_inside_preview_before_footer(monkeypatch) -> None:
    events: list[tuple[str, object, object] | str] = []
    context = {
        "adCopyEnabled": True,
        "adCopyPrompt": "한잔의 달콤한 혜택",
        "copyMode": "preserve",
    }
    fake_st = FakeStreamlit(
        {
            "result_bytes": b"generated-image",
            "result_context": context,
            "result_copy": None,
        }
    )

    def fake_render_image_preview(
        image_bytes: bytes,
        format_label: str,
        detail_label: str,
        *,
        summary_html: str = "",
    ) -> None:
        events.append(("preview", image_bytes, summary_html))

    def fake_result_copy_html(
        copy: dict[str, object] | None,
        result_context: dict[str, object] | None = None,
    ) -> str:
        events.append(("copy", copy, result_context))
        return '<div class="result-copy-panel">copy</div>'

    monkeypatch.setattr(result_panel, "st", fake_st)
    monkeypatch.setattr(result_panel, "render_image_preview", fake_render_image_preview)
    monkeypatch.setattr(result_panel, "result_copy_html", fake_result_copy_html)
    monkeypatch.setattr(
        result_panel,
        "_render_preview_history_controls",
        lambda **kwargs: events.append(("history", kwargs.get("copy_html"))),
    )

    result_panel.render_result_panel(
        is_generating=False,
        uploaded_file=None,
        format_label="인스타그램",
        detail_label="스토리 이미지",
    )

    assert events[0][0] == "preview"
    assert "result-summary-panel" in str(events[0][2])
    assert "광고 문구 포함" in str(events[0][2])
    assert all(event[0] != "summary" for event in events if isinstance(event, tuple))
    assert events[1] == ("copy", None, context)
    assert events[2] == ("history", '<div class="result-copy-panel">copy</div>')


def test_result_copy_does_not_fall_back_to_manual_ad_copy_prompt(monkeypatch) -> None:
    signature = inspect.signature(result_copy.render_result_copy)
    assert "result_context" in signature.parameters

    fake_st = FakeStreamlit()
    monkeypatch.setattr(result_copy, "st", fake_st)

    result_copy.render_result_copy(
        None,
        result_context={
            "adCopyEnabled": True,
            "adCopyPrompt": (
                "헤드라인: 한잔의 달콤한 혜택\n"
                "서브카피: 음료 할인으로 부담 없이 한잔의 여유를 즐겨보세요.\n"
                "CTA: 지금 주문하기"
            ),
            "copyMode": "preserve",
        },
    )

    html = "".join(fake_st.markdowns)
    assert "result-copy-panel" in html
    assert "입력 문구" not in html
    assert "result-copy-line" not in html
    assert "헤드라인" not in html
    assert "서브카피" not in html
    assert "CTA" not in html
    assert "한잔의 달콤한 혜택" not in html
    assert "음료 할인으로 부담 없이 한잔의 여유를 즐겨보세요." not in html
    assert "지금 주문하기" not in html


def test_result_copy_uses_context_mode_when_job_copy_has_no_mode(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(result_copy, "st", fake_st)

    result_copy.render_result_copy(
        {
            "headline": "오늘은 역시 레몬에이드!",
            "subcopy": "상큼하게 톡 쏘는 오늘의 선택",
            "cta": "지금 맛보기",
        },
        result_context={"adCopyEnabled": True, "copyMode": "polish"},
    )

    html = "".join(fake_st.markdowns)
    assert "자연스럽게 다듬기" in html
    assert "헤드라인" in html
    assert "서브카피" in html
    assert "CTA" in html
