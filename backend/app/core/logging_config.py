"""앱 전역 로깅 설정."""

import logging
import os
import sys

from backend.app.core.request_context import request_id_var

NOISY_LIBRARY_LOGGERS = ("PIL", "httpcore", "httpx", "openai")


class RequestIDFilter(logging.Filter):
    """현재 요청의 request_id를 모든 로그 레코드에 자동 주입한다."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging(_app_env: str) -> None:
    """앱 시작 시 한 번 호출. 전역 로거 포맷·레벨을 설정한다.

    기본은 INFO 레벨로 둔다. 자세한 디버깅이 필요하면 LOG_LEVEL=DEBUG로 올린다.
    uvicorn 액세스 로그는 우리 액세스 로그와 중복되므로 WARNING으로 낮춘다.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] req=%(request_id)s %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    for logger_name in NOISY_LIBRARY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
