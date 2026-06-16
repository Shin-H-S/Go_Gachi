"""인증/사용자 관련 라우트.

프론트가 Supabase로 로그인해 받은 토큰으로 '내 정보'를 확인하는 엔드포인트를 모은다.
로그인/회원가입 자체는 프론트가 Supabase와 직접 처리하고, 백엔드는 토큰 검증만 담당한다.
"""

from fastapi import APIRouter, Depends

from backend.app.api.mypage import router as mypage_router
from backend.app.core.auth import AuthUser, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])
router.include_router(mypage_router)


@router.get("/me")
async def read_me(user: AuthUser = Depends(get_current_user)) -> dict[str, str | None]:
    """현재 로그인한 사용자의 식별자/이메일/권한/표시 이름을 반환한다.

    Args:
        user: 토큰 검증을 통과한 로그인 사용자.
    Returns:
        dict: id, email, role, display_name.
    """
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "display_name": user.display_name,
    }
