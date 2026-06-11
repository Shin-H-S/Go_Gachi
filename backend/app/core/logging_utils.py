"""로그에 안전하게 박을 수 있게 식별자·민감정보를 가공하는 헬퍼."""


def mask_email(email: str | None) -> str:
    """이메일의 로컬 파트 앞 2자만 노출하고 나머지는 가린다.

    예: ``alice@example.com`` → ``al***@example.com``. 값이 없거나 형식이 잘못되면 ``***``.
    """
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    visible = local[:2] if local else ""
    return f"{visible}***@{domain}"


def mask_token(token: str | None) -> str:
    """JWT·access token의 앞 8자만 노출해 디버깅 식별용으로만 쓰게 만든다."""
    if not token:
        return "***"
    return f"{token[:8]}..."


def short_id(value: str | None, *, length: int = 8) -> str:
    """user_id·image_hash 같은 긴 식별자를 로그용 짧은 prefix로 줄인다(없으면 ``-``)."""
    if not value:
        return "-"
    return value[:length]
