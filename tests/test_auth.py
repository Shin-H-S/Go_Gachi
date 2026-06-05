import logging
from types import SimpleNamespace

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

    # HS256 경로가 jwt.decode까지 도달하려면 SUPABASE_JWT_SECRET이 채워져 있어야 한다.
    # CI에는 환경변수가 없으므로 검증 흐름만 확인할 수 있게 임의 값으로 채운다.
    settings = auth.get_settings()
    monkeypatch.setattr(settings, "supabase_jwt_secret", "test-secret")
    monkeypatch.setattr(auth.jwt, "get_unverified_header", lambda token: {"alg": "HS256"})
    monkeypatch.setattr(auth.jwt, "decode", fake_decode)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(HTTPException) as exc_info:
            auth.verify_supabase_jwt("expired-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "유효하지 않은 인증 토큰입니다."
    assert "Signature has expired" not in exc_info.value.detail
    assert "Signature has expired" in caplog.text


def test_verify_supabase_jwt_uses_jwks_for_asymmetric_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ES256/RS256 Supabase tokens are verified with the project's JWKS endpoint."""
    settings = auth.get_settings()
    monkeypatch.setattr(settings, "supabase_url", "https://project-ref.supabase.co")

    captured: dict[str, object] = {}

    class FakeJwksClient:
        def __init__(self, url: str) -> None:
            captured["jwks_url"] = url

        def get_signing_key_from_jwt(self, token: str):  # noqa: ANN201
            captured["token"] = token
            return SimpleNamespace(key="public-key")

    def fake_decode(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        captured["decode_args"] = args
        captured["decode_kwargs"] = kwargs
        return {"sub": "user-123", "email": "user@example.com"}

    monkeypatch.setattr(auth.jwt, "get_unverified_header", lambda token: {"alg": "ES256"})
    monkeypatch.setattr(auth.jwt, "PyJWKClient", FakeJwksClient)
    monkeypatch.setattr(auth.jwt, "decode", fake_decode)

    claims = auth.verify_supabase_jwt("jwt-token")

    assert claims["sub"] == "user-123"
    assert captured["jwks_url"] == ("https://project-ref.supabase.co/auth/v1/.well-known/jwks.json")
    assert captured["token"] == "jwt-token"
    assert captured["decode_args"] == ("jwt-token", "public-key")
    assert captured["decode_kwargs"] == {
        "algorithms": ["ES256"],
        "audience": "authenticated",
        "issuer": "https://project-ref.supabase.co/auth/v1",
    }
