from types import SimpleNamespace

import httpx

from frontend.services.api_client import GenerationResult
from frontend.work import generation


class FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def rerun(self) -> None:
        return None


def _run_generation(monkeypatch, fake_st: FakeStreamlit, fake_request_backend) -> None:
    monkeypatch.setattr(generation, "st", fake_st)
    monkeypatch.setattr(generation, "request_backend", fake_request_backend)
    monkeypatch.setattr(generation.time, "sleep", lambda seconds: None)

    generation.handle_generation_request(
        generate=True,
        uploaded_file=SimpleNamespace(getvalue=lambda: b"source-image"),
        prompt="make it bright",
        ad_copy_prompt="Fresh coffee",
        format_label="인스타그램",
        detail_label="정사각형 피드",
        current_result_context={"prompt": "make it bright"},
        ad_copy_enabled=True,
        copy_mode="preserve",
    )


def test_generation_request_passes_generation_options(monkeypatch) -> None:
    captured_kwargs: dict[str, object] = {}

    def fake_request_backend(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
        captured_kwargs.update(kwargs)
        return GenerationResult(image_bytes=b"result-image", copy=None)

    fake_st = FakeStreamlit()

    monkeypatch.setattr(generation, "st", fake_st)
    monkeypatch.setattr(generation, "request_backend", fake_request_backend)
    monkeypatch.setattr(generation.time, "sleep", lambda seconds: None)

    generation.handle_generation_request(
        generate=True,
        uploaded_file=SimpleNamespace(getvalue=lambda: b"source-image"),
        prompt="make it bright",
        ad_copy_prompt="Fresh coffee",
        format_label="인스타그램",
        detail_label="정사각형 피드",
        current_result_context={"prompt": "make it bright"},
        ad_copy_enabled=True,
        copy_mode="preserve",
    )

    assert "logo_file" not in captured_kwargs
    assert "logo_position" not in captured_kwargs
    assert captured_kwargs["copy_mode"] == "preserve"
    assert fake_st.session_state["result_bytes"] == b"result-image"


def test_generation_request_stores_existing_result_context(monkeypatch) -> None:
    def fake_request_backend(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
        return GenerationResult(
            image_bytes=b"result-image",
            copy=None,
        )

    fake_st = FakeStreamlit()

    monkeypatch.setattr(generation, "st", fake_st)
    monkeypatch.setattr(generation, "request_backend", fake_request_backend)
    monkeypatch.setattr(generation.time, "sleep", lambda seconds: None)

    generation.handle_generation_request(
        generate=True,
        uploaded_file=SimpleNamespace(getvalue=lambda: b"source-image"),
        prompt="make it bright",
        ad_copy_prompt="Fresh coffee",
        format_label="인스타그램",
        detail_label="정사각형 피드",
        current_result_context={"prompt": "make it bright"},
        ad_copy_enabled=True,
        copy_mode="preserve",
    )

    assert fake_st.session_state["result_context"] == {"prompt": "make it bright"}


def test_generation_request_shows_backend_string_detail(monkeypatch) -> None:
    request = httpx.Request("POST", "https://backend.example/api/generate")
    response = httpx.Response(
        400,
        json={"detail": "Mock image provider is disabled. Configure OpenAI."},
        request=request,
    )

    def fake_request_backend(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
        raise httpx.HTTPStatusError("bad request", request=request, response=response)

    fake_st = FakeStreamlit()

    _run_generation(monkeypatch, fake_st, fake_request_backend)

    assert fake_st.errors == [
        "백엔드 생성 요청 실패 [HTTP 400]: Mock image provider is disabled. Configure OpenAI."
    ]


def test_generation_request_uses_backend_detail_message(monkeypatch) -> None:
    request = httpx.Request("POST", "https://backend.example/api/generate")
    response = httpx.Response(
        503,
        json={
            "detail": {
                "code": "OPENAI_NOT_CONFIGURED",
                "message": "OpenAI API 키가 설정되지 않았습니다.",
            }
        },
        request=request,
    )

    def fake_request_backend(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
        raise httpx.HTTPStatusError("service unavailable", request=request, response=response)

    fake_st = FakeStreamlit()

    _run_generation(monkeypatch, fake_st, fake_request_backend)

    assert fake_st.errors == [
        "백엔드 설정 확인 필요 [HTTP 503]: OpenAI API 키가 설정되지 않았습니다."
    ]


def test_generation_request_falls_back_when_backend_detail_message_missing(
    monkeypatch,
) -> None:
    request = httpx.Request("POST", "https://backend.example/api/generate")
    response = httpx.Response(
        400,
        json={"detail": {"code": "VALIDATION_ERROR", "field": "targetWidth"}},
        request=request,
    )

    def fake_request_backend(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
        raise httpx.HTTPStatusError("bad request", request=request, response=response)

    fake_st = FakeStreamlit()

    _run_generation(monkeypatch, fake_st, fake_request_backend)

    assert fake_st.errors == [
        "백엔드 생성 요청 실패 [HTTP 400]: {'code': 'VALIDATION_ERROR', 'field': 'targetWidth'}"
    ]
