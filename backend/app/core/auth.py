"""Supabase Auth 기반 인증/권한 검증.

프론트가 Supabase로 로그인해 받은 access token(JWT)을 백엔드가 검증하고,
profiles 테이블에서 앱 권한(role)을 확인한다. 토큰의 alg에 따라 두 방식을 모두 지원한다.

  - ES256/RS256 (새 Supabase signing key): SUPABASE_URL로 JWKS를 조회해 공개키로 검증.
  - HS256 (기존 Legacy JWT Secret): SUPABASE_JWT_SECRET으로 대칭 키 검증.

SUPABASE_URL과 SUPABASE_JWT_SECRET 둘 다 비어 있으면 인증이 설정되지 않은 것으로 보고
보호 라우트에서 503을 돌려준다(현 단계 호환).
"""

import logging
import time
from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.config import get_settings
from backend.app.db import crud
from backend.app.db.database import async_session_scope

logger = logging.getLogger(__name__)

# auto_error=False: 토큰이 없어도 여기서 바로 401을 던지지 않고 의존성에서 직접 처리한다.
_bearer = HTTPBearer(auto_error=False)
ASYMMETRIC_JWT_ALGORITHMS = {"ES256", "RS256"}
LEGACY_JWT_ALGORITHMS = {"HS256"}
# Supabase가 signing key를 회전했을 때 우리 캐시가 영원히 옛 키에 묶이지 않도록
# PyJWKClient 인스턴스를 시간 윈도우 단위로 새로 만든다(1시간마다 새 인스턴스).
_JWKS_CACHE_TTL_SECONDS = 3600


@dataclass
class AuthUser:
    """검증된 로그인 사용자 1명의 핵심 정보."""

    id: str
    email: str | None
    role: str
    # 회원가입 시 입력한 표시 이름. 비어 있을 수 있어 화면에선 email로 폴백한다.
    display_name: str | None = None


def _supabase_issuer() -> str | None:
    """SUPABASE_URL로부터 Supabase가 발급한 토큰의 표준 issuer URL을 만든다.

    Returns:
        ``{SUPABASE_URL}/auth/v1`` 형태의 issuer, SUPABASE_URL 미설정이면 None.
    """
    settings = get_settings()
    supabase_url = settings.supabase_url.strip().rstrip("/")
    if not supabase_url:
        return None
    return f"{supabase_url}/auth/v1"


@lru_cache(maxsize=4)
def _jwks_client_cached(issuer: str, _epoch_window: int) -> jwt.PyJWKClient:
    """Supabase issuer × 시간 윈도우 단위로 PyJWKClient를 보관한다.

    ``_epoch_window``는 ``_jwks_client``가 현재 시각으로부터 계산해 넘긴다.
    시간 윈도우가 바뀌면 자연스럽게 새 인스턴스가 만들어지면서 JWKS를 다시 받는다.
    """
    return jwt.PyJWKClient(f"{issuer}/.well-known/jwks.json")


def _jwks_client(issuer: str) -> jwt.PyJWKClient:
    """현재 시간 윈도우에 해당하는 PyJWKClient를 돌려준다(키 회전 대비 TTL 적용)."""
    epoch_window = int(time.time() // _JWKS_CACHE_TTL_SECONDS)
    return _jwks_client_cached(issuer, epoch_window)


def _decode_asymmetric_supabase_jwt(token: str, algorithm: str) -> dict:
    """ES256/RS256 토큰을 Supabase의 JWKS 공개키로 검증한다.

    Supabase가 새로 도입한 signing key 방식에 대응한다. SUPABASE_URL이 없으면
    JWKS 엔드포인트를 만들 수 없어 검증이 불가능하다.
    """
    issuer = _supabase_issuer()
    if not issuer:
        raise jwt.InvalidIssuerError("SUPABASE_URL is required for JWKS JWT verification")

    jwks_client = _jwks_client(issuer)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=[algorithm],
        audience="authenticated",
        issuer=issuer,
    )


def _decode_legacy_supabase_jwt(token: str) -> dict:
    """HS256 토큰을 SUPABASE_JWT_SECRET(대칭 키)로 검증한다(레거시 호환).

    SUPABASE_URL이 함께 설정돼 있으면 issuer까지 같이 검증해 토큰 출처를 좁힌다.
    """
    settings = get_settings()
    if not settings.supabase_jwt_secret:
        raise jwt.InvalidKeyError("SUPABASE_JWT_SECRET is required for HS256 JWT verification")

    issuer = _supabase_issuer()
    kwargs: dict[str, str] = {"audience": "authenticated"}
    if issuer:
        kwargs["issuer"] = issuer
    return jwt.decode(
        token,
        settings.supabase_jwt_secret,
        algorithms=["HS256"],
        **kwargs,
    )


def _auth_verification_configured() -> bool:
    """JWT 검증에 필요한 설정이 최소 하나라도 들어있는지 본다.

    JWKS 방식은 SUPABASE_URL, 레거시는 SUPABASE_JWT_SECRET이 필요하다.
    둘 다 비어 있으면 백엔드는 보호 라우트에서 503을 돌려준다.
    """
    settings = get_settings()
    return bool(settings.supabase_url or settings.supabase_jwt_secret)


def verify_supabase_jwt(token: str) -> dict:
    """Supabase access token(JWT)을 검증해 claims를 반환한다.

    토큰 헤더의 alg에 따라 두 경로로 분기한다:
      - ES256/RS256: SUPABASE_URL의 JWKS 공개키로 검증(새 signing key 방식).
      - HS256: SUPABASE_JWT_SECRET 대칭 키로 검증(레거시 Legacy JWT Secret).

    Args:
        token: 프론트가 보낸 Bearer access token 문자열.
    Returns:
        검증된 JWT payload(claims) 딕셔너리.
    Raises:
        HTTPException(401): 서명/만료/issuer/형식·알고리즘이 잘못된 토큰.
    """
    try:
        header = jwt.get_unverified_header(token)
        algorithm = str(header.get("alg", ""))
        if algorithm in ASYMMETRIC_JWT_ALGORITHMS:
            return _decode_asymmetric_supabase_jwt(token, algorithm)
        if algorithm in LEGACY_JWT_ALGORITHMS:
            return _decode_legacy_supabase_jwt(token)
        raise jwt.InvalidAlgorithmError(f"Unsupported JWT algorithm: {algorithm}")
    except (jwt.PyJWTError, jwt.PyJWKClientError) as exc:
        logger.warning("invalid supabase jwt: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰입니다.",
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    """요청의 Bearer 토큰을 검증하고 프로필을 upsert해 로그인 사용자를 반환한다.

    SUPABASE_URL 또는 SUPABASE_JWT_SECRET 중 하나는 설정돼 있어야 동작한다(없으면 503).
    첫 로그인이면 프로필을 자동 생성하고(role='user'), 이후 요청에선 저장된 role을 그대로 읽는다.

    Args:
        credentials: Authorization 헤더에서 파싱된 Bearer 자격증명(없으면 None).
    Returns:
        검증된 AuthUser(id/email/role/display_name).
    Raises:
        HTTPException(401): 토큰 누락 또는 검증 실패.
        HTTPException(503): SUPABASE_URL과 SUPABASE_JWT_SECRET이 모두 미설정.
    """
    if not _auth_verification_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="인증이 아직 설정되지 않았습니다(SUPABASE_URL 또는 SUPABASE_JWT_SECRET 없음).",
        )
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다.",
        )

    claims = verify_supabase_jwt(credentials.credentials)
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에 사용자 식별자(sub)가 없습니다.",
        )
    email = claims.get("email")
    # 회원가입 시 sign_up options.data.display_name으로 넣은 값이 user_metadata에 따라온다.
    display_name = claims.get("user_metadata", {}).get("display_name")

    # 첫 로그인이면 프로필 생성(role='user'), 이후엔 메타데이터만 갱신하고 role 보존.
    async with async_session_scope() as db:
        profile = await crud.upsert_profile(
            db, user_id=user_id, email=email, display_name=display_name
        )
        role = profile.role
        # 마이페이지에서 바뀐 값을 반영하려면 JWT 토큰이 아니라 DB의 최신값을 사용한다.
        display_name = profile.display_name

    return AuthUser(id=user_id, email=email, role=role, display_name=display_name)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser | None:
    """로그인했으면 사용자를 반환하고, 비로그인/인증 미설정이면 None을 반환한다.

    로그인을 강제하지 않는 라우트(예: 생성)에서 "있으면 소유자로 기록"하는 용도다.
    토큰이 아예 없으면 None이지만, 토큰이 있는데 잘못됐으면 401로 막는다.

    Args:
        credentials: Authorization 헤더에서 파싱된 Bearer 자격증명(없으면 None).
    Returns:
        검증된 AuthUser, 비로그인/인증 미설정이면 None.
    Raises:
        HTTPException(401): 토큰이 있는데 검증에 실패한 경우.
    """
    # 인증 미설정(키 없음)이거나 토큰이 없으면 익명으로 통과시킨다.
    if not _auth_verification_configured() or credentials is None:
        return None
    return await get_current_user(credentials)


async def require_admin(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """로그인 사용자 중 role이 'admin'인 경우에만 통과시킨다.

    Args:
        user: get_current_user가 검증한 로그인 사용자.
    Returns:
        관리자 권한이 확인된 AuthUser.
    Raises:
        HTTPException(403): 관리자 권한이 아닐 때.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )
    return user
