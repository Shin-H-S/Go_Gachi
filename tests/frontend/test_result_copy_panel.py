from frontend.css.work_controls import WORK_CONTROLS_CSS
from frontend.css.work_preview import WORK_PREVIEW_CSS
from frontend.work import result_panel
from frontend.work.result_copy import result_copy_html


def test_result_copy_html_parses_backend_text_copy_into_detail_rows() -> None:
    html = result_copy_html(
        {
            "text": (
                "헤드라인: 한입의 달콤함\n"
                "서브카피: 줄을 설 만큼 부드러운 한 조각의 여유를 즐겨보세요.\n"
                "CTA: 지금 주문하기"
            ),
            "copyMode": "rewrite",
        },
        result_context={"adCopyEnabled": True},
    )

    assert "result-copy-empty" not in html
    assert "헤드라인" in html
    assert "한입의 달콤함" in html
    assert "서브카피" in html
    assert "줄을 설 만큼 부드러운 한 조각의 여유를 즐겨보세요." in html
    assert "CTA" in html
    assert "지금 주문하기" in html


def test_result_copy_html_omits_fallback_message_when_copy_fields_are_missing() -> None:
    html = result_copy_html(
        None,
        result_context={"adCopyEnabled": True, "copyMode": "rewrite"},
    )

    assert "result-copy-panel" in html
    assert "result-copy-mode" in html
    assert "result-copy-empty" not in html
    assert "자동 생성" not in html


def test_result_copy_html_does_not_use_manual_prompt_when_backend_copy_is_missing() -> None:
    html = result_copy_html(
        None,
        result_context={
            "adCopyEnabled": True,
            "copyMode": "rewrite",
            "adCopyPrompt": "headline: hidden headline\nsubcopy: hidden subcopy\nCTA: hidden cta",
        },
    )

    assert "result-copy-panel" in html
    assert "result-copy-line" not in html
    assert "hidden headline" not in html
    assert "hidden subcopy" not in html
    assert "hidden cta" not in html


def test_result_copy_panel_moves_up_without_changing_history_buttons() -> None:
    assert ".result-copy-panel" in WORK_PREVIEW_CSS
    assert "margin-top: -16px" in WORK_PREVIEW_CSS
    assert ".st-key-work-preview-undo" in WORK_CONTROLS_CSS
    assert ".st-key-work-preview-redo" in WORK_CONTROLS_CSS


def test_result_copy_panel_is_rendered_inside_history_controls_row(monkeypatch) -> None:
    events: list[object] = []

    class FakeColumn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

    class FakeStreamlit:
        def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
            events.append(("markdown", body, unsafe_allow_html))

        def container(self, *, key: str):
            events.append(("container", key))
            return FakeColumn()

        def columns(self, spec, *, gap=None, vertical_alignment=None):
            events.append(("columns", spec, gap, vertical_alignment))
            return [FakeColumn(), FakeColumn(), FakeColumn(), FakeColumn()]

        def button(self, *args, **kwargs) -> bool:
            events.append(("button", kwargs.get("key")))
            return False

    monkeypatch.setattr(result_panel, "st", FakeStreamlit())
    monkeypatch.setattr(result_panel, "_render_preview_history_css", lambda: None)

    result_panel._render_preview_history_controls(
        copy_html='<div class="result-copy-panel">copy</div>',
        cursor=1,
        total=1,
    )

    assert ("columns", [0.12, 0.12, 0.36, 0.40], "small", "top") in events
    assert ("button", "work-preview-undo") in events
    assert ("button", "work-preview-redo") in events
    assert ("markdown", '<div class="result-copy-panel">copy</div>', True) in events
