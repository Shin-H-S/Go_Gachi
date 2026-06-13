import httpx

from frontend.services.backend_errors import (
    extract_backend_error_info,
    format_backend_http_error,
)


def _status_error(status_code: int, payload: object) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://backend.example/api/generate")
    response = httpx.Response(status_code, json=payload, request=request)
    return httpx.HTTPStatusError("backend error", request=request, response=response)


def test_extract_backend_error_info_uses_object_detail_message() -> None:
    error_info = extract_backend_error_info(
        _status_error(
            503,
            {
                "detail": {
                    "code": "OPENAI_NOT_CONFIGURED",
                    "message": "OpenAI API 키가 설정되지 않았습니다.",
                }
            },
        )
    )

    assert error_info.message == "OpenAI API 키가 설정되지 않았습니다."
    assert error_info.code == "OPENAI_NOT_CONFIGURED"


def test_extract_backend_error_info_keeps_string_detail() -> None:
    error_info = extract_backend_error_info(
        _status_error(400, {"detail": "지원하지 않는 detailType입니다."})
    )

    assert error_info.message == "지원하지 않는 detailType입니다."
    assert error_info.code is None


def test_format_backend_http_error_uses_setup_title_for_setup_codes() -> None:
    error_message = format_backend_http_error(
        _status_error(
            503,
            {
                "detail": {
                    "code": "OPENAI_NOT_CONFIGURED",
                    "message": "OpenAI API 키가 설정되지 않았습니다.",
                }
            },
        ),
        default_title="백엔드 생성 요청 실패",
    )

    assert error_message == (
        "백엔드 설정 확인 필요 [HTTP 503]: OpenAI API 키가 설정되지 않았습니다."
    )
