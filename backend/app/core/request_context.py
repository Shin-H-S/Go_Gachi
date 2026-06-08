"""요청 단위 컨텍스트(현재 request_id)를 보관해 로깅 헬퍼와 공유한다."""

import contextvars

# 미들웨어가 요청 진입 시 set, 종료 시 reset 한다. 기본값 "-"은 미들웨어 밖에서
# 발생하는 로그(앱 시작 시 등)를 구분하기 위함.
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id",
    default="-",
)
