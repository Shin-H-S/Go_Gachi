import importlib


class FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.buttons: list[dict[str, object]] = []

    def button(self, label: str, **kwargs) -> bool:
        self.buttons.append({"label": label, **kwargs})
        return False

    def download_button(self, label: str, **kwargs) -> None:
        self.buttons.append({"label": label, **kwargs})

    def link_button(self, label: str, url: str, **kwargs) -> None:
        self.buttons.append({"label": label, "url": url, **kwargs})

    def rerun(self) -> None:
        return None

    def error(self, message: str) -> None:  # noqa: ARG002
        return None


def test_work_header_uses_signed_download_link_when_available(monkeypatch) -> None:
    header = importlib.import_module("frontend.work.header")
    fake_st = FakeStreamlit()
    fake_st.session_state["result_download_url"] = "https://signed.example/result.png"

    monkeypatch.setattr(header, "st", fake_st)

    header._render_header_download_button()

    link_button = next(
        button for button in fake_st.buttons if button.get("key") == "work-header-download-link"
    )
    assert link_button["url"] == "https://signed.example/result.png"
    assert not any(button.get("key") == "work-header-download-fetch" for button in fake_st.buttons)


def test_work_header_falls_back_to_fetch_button_without_signed_download_url(monkeypatch) -> None:
    header = importlib.import_module("frontend.work.header")
    fake_st = FakeStreamlit()
    fake_st.session_state["result_image_url"] = "https://assets.example/result.png"

    monkeypatch.setattr(header, "st", fake_st)

    header._render_header_download_button()

    fetch_button = next(
        button for button in fake_st.buttons if button.get("key") == "work-header-download-fetch"
    )
    assert fetch_button["label"] == "⇩ 다운로드"
