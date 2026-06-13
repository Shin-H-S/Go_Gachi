"""요청 추적·액세스 로깅용 HTTP 미들웨어."""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.app.core.request_context import request_id_var

logger = logging.getLogger("backend.access")

_CallNext = Callable[[Request], Awaitable[Response]]


class AccessLogMiddleware(BaseHTTPMiddleware):
    """모든 요청의 method·path·status·소요시간을 한 줄 로그로 남긴다."""

    async def dispatch(self, request: Request, call_next: _CallNext) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "%s %s failed after %.1fms",
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        if request.url.path == "/api/health":
            return response

        logger.info(
            "%s %s status=%d took=%.1fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """요청마다 X-Request-ID를 발급해 ContextVar와 응답 헤더에 동시에 노출한다."""

    async def dispatch(self, request: Request, call_next: _CallNext) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        except Exception:
            # 라우트가 예외를 던져도 X-Request-ID는 클라이언트에 돌려줘 디버깅을 돕는다.
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)

        response.headers["X-Request-ID"] = request_id
        return response
