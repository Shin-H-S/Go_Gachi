import ast
import base64
from pathlib import Path
from types import SimpleNamespace

import pytest

from frontend import api_client
from frontend.work import copy_controls

ROOT_DIR = Path(__file__).resolve().parents[2]
WORK_PAGE = ROOT_DIR / "frontend" / "pages" / "work.py"
WORK_COMPONENTS = ROOT_DIR / "frontend" / "work" / "components.py"
COPY_CONTROLS = ROOT_DIR / "frontend" / "work" / "copy_controls.py"
RESULT_PANEL = ROOT_DIR / "frontend" / "work" / "result_panel.py"


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


class FakeCopyControlStreamlit:
    def __init__(self, *, checkbox_value: bool) -> None:
        self.checkbox_value = checkbox_value
        self.session_state = {}
        self.text_area_calls: list[dict[str, object]] = []
        self.button_calls: list[dict[str, object]] = []
        self.radio_calls: list[dict[str, object]] = []
        self.info_messages: list[str] = []

    def checkbox(self, *args, **kwargs) -> bool:
        return self.checkbox_value

    def text_area(self, *args, **kwargs) -> str:
        self.text_area_calls.append({"args": args, "kwargs": kwargs})
        return "직접 입력한 문구"

    def button(self, *args, **kwargs) -> bool:
        self.button_calls.append({"args": args, "kwargs": kwargs})
        return False

    def radio(self, *args, **kwargs) -> str:
        self.radio_calls.append({"args": args, "kwargs": kwargs})
        return "원본대로 유지하기"

    def info(self, message: str) -> None:
        self.info_messages.append(message)


def _keyword(call: ast.Call, name: str) -> ast.keyword | None:
    return next((keyword for keyword in call.keywords if keyword.arg == name), None)


def test_copy_controls_render_ad_copy_checkbox_checked_by_default() -> None:
    tree = ast.parse(COPY_CONTROLS.read_text(encoding="utf-8"))
    checkbox_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "checkbox"
    ]

    ad_copy_call = next(
        (
            call
            for call in checkbox_calls
            if (_keyword(call, "key") is not None)
            and isinstance(_keyword(call, "key").value, ast.Constant)
            and _keyword(call, "key").value.value == "ad_copy_enabled"
        ),
        None,
    )

    assert ad_copy_call is not None
    default_value = _keyword(ad_copy_call, "value")
    assert isinstance(default_value, ast.keyword)
    assert isinstance(default_value.value, ast.Constant)
    assert default_value.value.value is True


def test_copy_controls_do_not_render_redundant_ad_copy_section_heading() -> None:
    source = COPY_CONTROLS.read_text(encoding="utf-8")

    assert '<p class="section-label">광고 문구</p>' not in source
    assert '"광고 문구 포함"' in source


def test_copy_controls_do_not_render_auto_copy_button() -> None:
    source = COPY_CONTROLS.read_text(encoding="utf-8")
    tree = ast.parse(source)
    button_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "button"
    ]
    auto_copy_button = next(
        (
            call
            for call in button_calls
            if (_keyword(call, "key") is not None)
            and isinstance(_keyword(call, "key").value, ast.Constant)
            and _keyword(call, "key").value.value == "auto_copy_generate"
        ),
        None,
    )

    assert auto_copy_button is None
    assert "request_auto_copy" not in source
    assert "build_auto_copy" not in source


def test_copy_controls_render_manual_copy_prompt_state_key() -> None:
    source = COPY_CONTROLS.read_text(encoding="utf-8")
    tree = ast.parse(source)
    prompt_text_area = next(
        (
            call
            for call in ast.walk(tree)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "text_area"
            and (_keyword(call, "key") is not None)
            and isinstance(_keyword(call, "key").value, ast.Constant)
            and _keyword(call, "key").value.value == "ad_copy_prompt"
        ),
        None,
    )

    assert prompt_text_area is not None


def test_copy_controls_hide_copy_inputs_when_text_overlay_is_unchecked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_st = FakeCopyControlStreamlit(checkbox_value=False)
    monkeypatch.setattr(copy_controls, "st", fake_st)

    prompt, text_overlay_enabled, copy_mode = copy_controls.render_copy_controls(
        "인스타그램",
        "정사각형 피드",
        "밝은 배경",
    )

    assert prompt == ""
    assert text_overlay_enabled is False
    assert copy_mode == "preserve"
    assert fake_st.text_area_calls == []
    assert fake_st.button_calls == []
    assert fake_st.radio_calls == []
    assert "auto_copy_status" not in fake_st.session_state


def test_copy_controls_render_manual_copy_mode_selector() -> None:
    source = COPY_CONTROLS.read_text(encoding="utf-8")
    tree = ast.parse(source)
    radio_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "radio"
    ]

    copy_mode_radio = next(
        (
            call
            for call in radio_calls
            if (_keyword(call, "key") is not None)
            and isinstance(_keyword(call, "key").value, ast.Constant)
            and _keyword(call, "key").value.value == "copy_mode_label"
        ),
        None,
    )

    assert copy_mode_radio is not None
    assert "COPY_MODE_OPTIONS" in source
    assert '"광고 문구 다듬기 옵션"' in source
    assert '"문구 처리 방식"' not in source


def test_work_page_keeps_image_prompt_separate_from_ad_copy() -> None:
    source = WORK_PAGE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    text_area_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "text_area"
    ]

    image_prompt = next(
        (
            call
            for call in text_area_calls
            if (_keyword(call, "key") is not None)
            and isinstance(_keyword(call, "key").value, ast.Constant)
            and _keyword(call, "key").value.value == "image_prompt"
        ),
        None,
    )

    assert image_prompt is not None
    assert "이미지 요청사항" in source
    assert "프롬프트" not in source


def test_work_page_displays_backend_copy_metadata() -> None:
    work_source = WORK_PAGE.read_text(encoding="utf-8")
    result_panel_source = RESULT_PANEL.read_text(encoding="utf-8")

    assert "from frontend.work.result_panel import render_result_panel" in work_source
    assert "from frontend.work.result_copy import result_copy_html" in result_panel_source
    assert 'st.session_state.get("result_copy")' in result_panel_source
    assert "result_copy_html(" in result_panel_source
    assert "_render_preview_history_controls(copy_html=copy_html)" in result_panel_source


def test_work_page_displays_result_inclusion_summary() -> None:
    work_source = WORK_PAGE.read_text(encoding="utf-8")
    result_panel_source = RESULT_PANEL.read_text(encoding="utf-8")

    assert "from frontend.work.result_panel import render_result_panel" in work_source
    assert "from frontend.work.result_summary import result_summary_html" in result_panel_source
    assert 'st.session_state.get("result_context")' in result_panel_source
    assert "summary_html=summary_html" in result_panel_source


def test_work_page_moves_download_and_history_controls_to_result_panel() -> None:
    work_source = WORK_PAGE.read_text(encoding="utf-8")
    components_source = WORK_COMPONENTS.read_text(encoding="utf-8")
    result_panel_source = RESULT_PANEL.read_text(encoding="utf-8")

    assert "tool-row" not in work_source
    assert "request_asset_bytes" not in work_source
    assert "undo_clicked" not in work_source
    assert "redo_clicked" not in work_source
    assert "_render_header_download_button(" in components_source
    assert "request_asset_bytes" in components_source
    assert 'key="work-header-download-button"' in components_source
    assert 'key="work-header-download-fetch"' in components_source
    assert 'key="work-header-download-empty"' in components_source
    assert "disabled=True" in components_source
    assert "_render_download_action(" not in result_panel_source
    assert "result-download" not in result_panel_source
    assert "request_asset_bytes" not in result_panel_source
    assert "_render_preview_history_controls(" in result_panel_source
    assert "if is_generating:" in result_panel_source
    assert 'key="work-preview-undo"' in result_panel_source
    assert 'key="work-preview-redo"' in result_panel_source


def test_request_backend_sends_ad_copy_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_json: dict[str, object] = {}

    def fake_post(
        url: str,  # noqa: ARG001
        json: dict[str, object],
        headers: dict[str, str],  # noqa: ARG001
        timeout: int,  # noqa: ARG001
    ) -> FakeResponse:
        captured_json.update(json)
        return FakeResponse({"imageDataUrl": "data:image/png;base64,cmVzdWx0"})

    uploaded_file = SimpleNamespace(type="image/png", getvalue=lambda: b"source-image")
    monkeypatch.setattr(api_client, "BACKEND_URL", "https://backend.example")
    monkeypatch.setattr(api_client.httpx, "post", fake_post)

    result = api_client.request_backend(
        uploaded_file,
        "",
        "인스타그램",
        "정사각형 피드",
        ad_copy_enabled=False,
    )

    assert result.image_bytes == b"result"
    assert captured_json["imageDataUrl"] == (
        f"data:image/png;base64,{base64.b64encode(b'source-image').decode('ascii')}"
    )
    assert captured_json["adCopyEnabled"] is False
    assert captured_json["userCopy"] == ""
