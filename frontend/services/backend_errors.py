from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class BackendErrorInfo:
    message: str
    code: str | None = None


SETUP_ERROR_CODES = {
    "OPENAI_NOT_CONFIGURED",
    "OPENAI_API_KEY_MISSING",
    "IMAGE_PROVIDER_NOT_CONFIGURED",
    "MOCK_PROVIDER_DISABLED",
}


def extract_backend_error_info(exc: httpx.HTTPStatusError) -> BackendErrorInfo:
    try:
        payload = exc.response.json()
    except ValueError:
        return BackendErrorInfo(exc.response.text)

    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str):
            return BackendErrorInfo(detail)
        if isinstance(detail, dict):
            message = detail.get("message")
            code = detail.get("code")
            return BackendErrorInfo(
                str(message) if message else str(detail),
                str(code) if code else None,
            )
        if detail is not None:
            return BackendErrorInfo(str(detail))

    return BackendErrorInfo(exc.response.text)


def backend_error_title(
    error_info: BackendErrorInfo,
    *,
    default_title: str,
) -> str:
    if error_info.code in SETUP_ERROR_CODES:
        return "백엔드 설정 확인 필요"
    return default_title


def format_backend_http_error(
    exc: httpx.HTTPStatusError,
    *,
    default_title: str,
) -> str:
    error_info = extract_backend_error_info(exc)
    title = backend_error_title(error_info, default_title=default_title)
    return f"{title} [HTTP {exc.response.status_code}]: {error_info.message}"
