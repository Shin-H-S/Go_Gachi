import logging
import os

from backend.app.core.logging_config import NOISY_LIBRARY_LOGGERS, RequestIDFilter, setup_logging
from backend.app.core.logging_utils import mask_email, mask_token, short_id
from backend.app.core.request_context import request_id_var


def test_request_id_filter_injects_current_context_value() -> None:
    token = request_id_var.set("req-test-123")
    try:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="message",
            args=(),
            exc_info=None,
        )

        assert RequestIDFilter().filter(record)
        assert record.request_id == "req-test-123"
    finally:
        request_id_var.reset(token)


def test_setup_logging_replaces_root_handler() -> None:
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    original_log_level = os.environ.pop("LOG_LEVEL", None)
    original_library_levels = {
        logger_name: logging.getLogger(logger_name).level for logger_name in NOISY_LIBRARY_LOGGERS
    }

    try:
        setup_logging("local")

        assert root.level == logging.INFO
        assert len(root.handlers) == 1
        assert any(isinstance(filter_, RequestIDFilter) for filter_ in root.handlers[0].filters)
        assert all(
            logging.getLogger(logger_name).level == logging.WARNING
            for logger_name in NOISY_LIBRARY_LOGGERS
        )
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)
        if original_log_level is not None:
            os.environ["LOG_LEVEL"] = original_log_level
        for logger_name, level in original_library_levels.items():
            logging.getLogger(logger_name).setLevel(level)


def test_setup_logging_can_enable_debug_with_env() -> None:
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level
    original_log_level = os.environ.get("LOG_LEVEL")

    try:
        os.environ["LOG_LEVEL"] = "DEBUG"
        setup_logging("local")

        assert root.level == logging.DEBUG
    finally:
        root.handlers = original_handlers
        root.setLevel(original_level)
        if original_log_level is None:
            os.environ.pop("LOG_LEVEL", None)
        else:
            os.environ["LOG_LEVEL"] = original_log_level


def test_logging_utils_mask_sensitive_values() -> None:
    assert mask_email("yejin@example.com") == "ye***@example.com"
    assert mask_email(None) == "***"
    assert mask_token("abcdefghijklmnopqrstuvwxyz") == "abcdefgh..."
    assert short_id("1234567890") == "12345678"
