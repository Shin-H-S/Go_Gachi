from frontend.work.result_summary import render_result_summary


class FakeStreamlit:
    def __init__(self) -> None:
        self.markdowns: list[str] = []

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        assert unsafe_allow_html is True
        self.markdowns.append(body)


def test_result_summary_renders_ad_copy_included(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr("frontend.work.result_summary.st", fake_st)

    render_result_summary({"adCopyEnabled": True})

    html = "".join(fake_st.markdowns)
    assert "result-summary-panel" in html
    assert "광고 문구 포함" in html
    assert "로고" not in html


def test_result_summary_renders_ad_copy_excluded(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr("frontend.work.result_summary.st", fake_st)

    render_result_summary({"adCopyEnabled": False})

    html = "".join(fake_st.markdowns)
    assert "광고 문구 미포함" in html
    assert "로고" not in html


def test_result_summary_ignores_legacy_logo_metadata(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr("frontend.work.result_summary.st", fake_st)

    render_result_summary(
        {
            "adCopyEnabled": True,
            "logoUploadHash": "uploaded-logo",
            "logo": {"used": False, "position": "top_right"},
        }
    )

    html = "".join(fake_st.markdowns)
    assert "logo.used" not in html
    assert "logo.position" not in html
    assert "로고" not in html


def test_result_summary_skips_empty_context(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr("frontend.work.result_summary.st", fake_st)

    render_result_summary(None)

    assert fake_st.markdowns == []
