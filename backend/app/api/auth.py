"""인증/사용자 관련 라우트.

프론트가 Supabase로 로그인해 받은 토큰으로 '내 정보'를 확인하는 엔드포인트를 모은다.
로그인/회원가입 자체는 프론트가 Supabase와 직접 처리하고, 백엔드는 토큰 검증만 담당한다.
"""

from fastapi import APIRouter, Depends

from backend.app.core.auth import AuthUser, get_current_user
from backend.app.core.config import get_settings
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.services.storage_url import public_output_url

router = APIRouter(prefix="/api/auth", tags=["auth"])


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


@router.get("/me/generations")
async def read_my_generations(
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    """현재 로그인한 사용자가 만든 생성 기록을 최신순으로 반환한다 ("내 작업 기록").

    Args:
        user: 토큰 검증을 통과한 로그인 사용자.
    Returns:
        dict: items(생성 기록 리스트)와 count(개수).
    """
    # BASE_URL이 환경마다 다르므로 DB 값(있어도) 신뢰하지 않고 매번 현재 BASE_URL로 재계산한다.
    # GCS·고정 도메인으로 이전한 뒤에는 DB의 image_url을 그대로 신뢰하도록 바꿀 수 있다.
    settings = get_settings()
    async with async_session_scope() as db:
        rows = await crud.list_user_generations(db, user.id)
        items = [
            {
                "request_id": row.request_id,
                "preset_id": row.preset_id,
                "status": row.status,
                "image_url": public_output_url(settings, row.output_path),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    return {"items": items, "count": len(items)}
