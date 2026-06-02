import logging

import jwt
import pytest
from fastapi import HTTPException

from backend.app.core import auth


def test_verify_supabase_jwt_hides_provider_error_detail(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """프론트 응답에는 고정 문구만 보내고, 자세한 JWT 실패 원인은 서버 로그에 남긴다."""

    def fake_decode(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        raise jwt.ExpiredSignatureError("Signature has expired")

    monkeypatch.setattr(auth.jwt, "decode", fake_decode)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(HTTPException) as exc_info:
            auth.verify_supabase_jwt("expired-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "유효하지 않은 인증 토큰입니다."
    assert "Signature has expired" not in exc_info.value.detail
    assert "Signature has expired" in caplog.text
