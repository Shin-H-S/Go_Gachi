from frontend.work.result_summary import render_result_summary


class FakeStreamlit:
    def __init__(self) -> None:
        self.markdowns: list[str] = []

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        assert unsafe_allow_html is True
        self.markdowns.append(body)


def test_result_summary_renders_ad_copy_status_only(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr("frontend.work.result_summary.st", fake_st)

    render_result_summary(
        {
            "adCopyEnabled": True,
            "logoUploadHash": "legacy-logo-hash",
            "logo": {"used": True, "position": "bottom_right"},
        }
    )

    html = "".join(fake_st.markdowns)
    assert "result-summary-panel" in html
    assert "logo" not in html.lower()
    assert "로고" not in html


def test_result_summary_skips_empty_context(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr("frontend.work.result_summary.st", fake_st)

    render_result_summary(None)

    assert fake_st.markdowns == []
