"""Auth and current-user routes."""

from fastapi import APIRouter, Depends

from backend.app.api.mypage import router as mypage_router
from backend.app.core.auth import AuthUser, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])
router.include_router(mypage_router)


@router.get("/me")
async def read_me(user: AuthUser = Depends(get_current_user)) -> dict[str, str | None]:
    """Return the currently authenticated user."""
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "display_name": user.display_name,
    }
