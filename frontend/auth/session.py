import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

FRONTEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = FRONTEND_DIR.parent


class AuthConfigurationError(RuntimeError):
    """Raised when Supabase frontend credentials are not configured."""


class AuthLoginError(RuntimeError):
    """Raised when Supabase does not return a usable login session."""


class AuthSignupError(RuntimeError):
    """Raised when Supabase signup cannot be completed."""


@dataclass(frozen=True)
class EmailAuthSession:
    access_token: str
    user_id: str
    email: str


@dataclass(frozen=True)
class EmailSignupResult:
    user_id: str
    email: str
    display_name: str


def load_auth_env() -> None:
    load_dotenv(ROOT_DIR / ".env", override=False)
    load_dotenv(FRONTEND_DIR / ".env", override=False)


def get_supabase_client():
    load_auth_env()
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()

    if not supabase_url or not supabase_anon_key:
        raise AuthConfigurationError(
            "Supabase 로그인 설정이 없습니다. SUPABASE_URL과 SUPABASE_ANON_KEY를 설정해주세요."
        )

    return create_client(supabase_url, supabase_anon_key)


def login_with_email(email: str, password: str, supabase_client=None) -> EmailAuthSession:
    client = supabase_client or get_supabase_client()
    normalized_email = email.strip()

    try:
        response = client.auth.sign_in_with_password(
            {"email": normalized_email, "password": password}
        )
    except Exception as exc:
        raise AuthLoginError("이메일 또는 비밀번호를 확인해주세요.") from exc

    session = getattr(response, "session", None)
    user = getattr(response, "user", None)
    access_token = getattr(session, "access_token", "")

    if not session or not access_token or not user:
        raise AuthLoginError("로그인 세션을 받을 수 없습니다. 다시 로그인해주세요.")

    return EmailAuthSession(
        access_token=access_token,
        user_id=str(getattr(user, "id", "")),
        email=str(getattr(user, "email", normalized_email) or normalized_email),
    )


def signup_with_email(
    email: str,
    password: str,
    display_name: str,
    supabase_client=None,
) -> EmailSignupResult:
    normalized_email = email.strip()
    normalized_display_name = display_name.strip()

    if not normalized_email:
        raise AuthSignupError("이메일을 입력해주세요.")
    if len(password) < 8:
        raise AuthSignupError("비밀번호는 8자 이상 입력해주세요.")
    if not normalized_display_name:
        raise AuthSignupError("닉네임을 입력해주세요.")

    client = supabase_client or get_supabase_client()
    payload = {
        "email": normalized_email,
        "password": password,
        "options": {"data": {"display_name": normalized_display_name}},
    }

    try:
        response = client.auth.sign_up(payload)
    except Exception as exc:
        raise AuthSignupError("회원가입 정보를 확인해주세요.") from exc

    user = getattr(response, "user", None)
    user_id = str(getattr(user, "id", "") if user else "")
    user_email = str(getattr(user, "email", normalized_email) if user else normalized_email)

    return EmailSignupResult(
        user_id=user_id,
        email=user_email,
        display_name=normalized_display_name,
    )


def save_auth_session(session_state, auth_session: EmailAuthSession) -> None:
    session_state["is_logged_in"] = True
    session_state["auth_access_token"] = auth_session.access_token
    session_state["auth_user_id"] = auth_session.user_id
    session_state["auth_user_email"] = auth_session.email
    session_state["auth_error"] = ""
    session_state["auth_notice"] = ""


def clear_auth_session(session_state, notice: str = "") -> None:
    session_state["is_logged_in"] = False
    session_state["auth_access_token"] = ""
    session_state["auth_user_id"] = ""
    session_state["auth_user_email"] = ""
    session_state["auth_error"] = ""
    session_state["auth_notice"] = notice
