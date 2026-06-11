import httpx

from frontend.work import copy_controls


class FakeStreamlit:
    def __init__(self) -> None:
        self.session_state: dict[str, object] = {}


def test_auto_copy_error_status_uses_backend_detail_message(monkeypatch) -> None:
    request = httpx.Request("POST", "https://backend.example/api/copy")
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

    def fake_request_auto_copy(*args, **kwargs):  # noqa: ANN002, ANN003, ARG001
        raise httpx.HTTPStatusError(
            "service unavailable",
            request=request,
            response=response,
        )

    fake_st = FakeStreamlit()
    monkeypatch.setattr(copy_controls, "st", fake_st)
    monkeypatch.setattr(copy_controls, "request_auto_copy", fake_request_auto_copy)

    copy_controls._fill_auto_copy(
        format_label="인스타그램",
        detail_label="정사각형 피드",
        image_prompt="밝게",
    )

    assert fake_st.session_state["auto_copy_status"] == (
        "백엔드 설정 확인 필요 [HTTP 503]: OpenAI API 키가 설정되지 않았습니다."
    )
