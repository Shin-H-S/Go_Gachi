import base64
from types import SimpleNamespace

from frontend.work import logo_controls


class FakeStreamlit:
    def __init__(self, uploaded_file=None) -> None:
        self.uploaded_file = uploaded_file
        self.markdowns: list[dict[str, object]] = []
        self.file_uploader_calls: list[dict[str, object]] = []
        self.selectbox_calls: list[dict[str, object]] = []

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append(
            {
                "body": body,
                "unsafe_allow_html": unsafe_allow_html,
            }
        )

    def file_uploader(self, label: str, **kwargs):
        self.file_uploader_calls.append({"label": label, "kwargs": kwargs})
        return self.uploaded_file

    def selectbox(self, label: str, **kwargs):
        self.selectbox_calls.append({"label": label, "kwargs": kwargs})
        options = kwargs["options"]
        return options[kwargs["index"]]


def _fake_logo_file(content: bytes = b"logo-bytes", mime_type: str = "image/webp"):
    return SimpleNamespace(type=mime_type, getvalue=lambda: content)


def test_logo_preview_renders_uploaded_logo_as_contained_data_url(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    logo_file = _fake_logo_file()
    expected_data_url = "data:image/webp;base64," + base64.b64encode(b"logo-bytes").decode("ascii")

    monkeypatch.setattr(logo_controls, "st", fake_st)

    logo_controls.render_logo_preview(logo_file)

    assert len(fake_st.markdowns) == 1
    rendered_html = fake_st.markdowns[0]["body"]
    assert fake_st.markdowns[0]["unsafe_allow_html"] is True
    assert "logo-preview-frame" in rendered_html
    assert "<img" in rendered_html
    assert expected_data_url in rendered_html
    assert "logo-preview-placeholder" not in rendered_html


def test_logo_preview_renders_placeholder_without_logo(monkeypatch) -> None:
    fake_st = FakeStreamlit()
    monkeypatch.setattr(logo_controls, "st", fake_st)

    logo_controls.render_logo_preview(None)

    rendered_html = fake_st.markdowns[0]["body"]
    assert "logo-preview-frame" in rendered_html
    assert "logo-preview-placeholder" in rendered_html
    assert "<img" not in rendered_html


def test_logo_controls_enforce_single_logo_upload_and_default_position(monkeypatch) -> None:
    uploaded_logo = _fake_logo_file()
    fake_st = FakeStreamlit(uploaded_file=uploaded_logo)
    monkeypatch.setattr(logo_controls, "st", fake_st)

    logo_file, logo_position = logo_controls.render_logo_controls()

    assert logo_file is uploaded_logo
    assert logo_position == "bottom_right"

    uploader = fake_st.file_uploader_calls[0]
    assert uploader["kwargs"]["type"] == logo_controls.UPLOAD_FILE_TYPES
    assert uploader["kwargs"]["accept_multiple_files"] is False
    assert uploader["kwargs"]["key"] == "logo_upload"

    selectbox = fake_st.selectbox_calls[0]
    assert selectbox["kwargs"]["options"] == logo_controls.LOGO_POSITION_OPTIONS
    assert selectbox["kwargs"]["index"] == logo_controls.LOGO_POSITION_OPTIONS.index("bottom_right")


def test_logo_controls_hide_extra_add_button_but_keep_remove_button(monkeypatch) -> None:
    fake_st = FakeStreamlit(uploaded_file=_fake_logo_file())
    monkeypatch.setattr(logo_controls, "st", fake_st)

    logo_controls.render_logo_controls()

    injected_html = "\n".join(str(call["body"]) for call in fake_st.markdowns)
    normalized_html = " ".join(injected_html.split())
    assert 'div:not(:has([data-testid="stFileUploaderFile"])) button' in injected_html
    assert "display: none !important;" in injected_html
    assert 'div:has([data-testid="stFileUploaderFile"]) button' in injected_html
    assert "display: inline-flex !important;" in injected_html
    assert ".st-key-logo_upload section button { display: none !important;" not in normalized_html


def test_logo_controls_do_not_inject_upload_button_css_without_logo(monkeypatch) -> None:
    fake_st = FakeStreamlit(uploaded_file=None)
    monkeypatch.setattr(logo_controls, "st", fake_st)

    logo_file, logo_position = logo_controls.render_logo_controls()

    injected_html = "\n".join(str(call["body"]) for call in fake_st.markdowns)
    assert logo_file is None
    assert logo_position == "bottom_right"
    assert 'div:not(:has([data-testid="stFileUploaderFile"])) button' not in injected_html
    assert "display: none !important;" not in injected_html
