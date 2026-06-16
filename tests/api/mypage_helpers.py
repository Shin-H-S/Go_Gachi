from backend.app.core.auth import AuthUser


def user(user_id: str = "user-check") -> AuthUser:
    return AuthUser(
        id=user_id,
        email=f"{user_id}@example.com",
        role="user",
        display_name="User",
    )
