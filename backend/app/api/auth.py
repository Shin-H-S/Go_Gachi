"""인증/사용자 관련 라우트.

프론트가 Supabase로 로그인해 받은 토큰으로 '내 정보'를 확인하는 엔드포인트를 모은다.
로그인/회원가입 자체는 프론트가 Supabase와 직접 처리하고, 백엔드는 토큰 검증만 담당한다.
"""

import asyncio

from fastapi import APIRouter, Depends

from backend.app.core.auth import AuthUser, get_current_user
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.services.storage_url import public_output_url_if_exists_async

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
    # DB에는 환경별 호스트를 저장하지 않고, 응답할 때 /outputs/... 경로를 만든다.
    async with async_session_scope() as db:
        rows = await crud.list_user_generations(db, user.id)

    image_urls = await asyncio.gather(
        *(public_output_url_if_exists_async(row.output_path) for row in rows)
    )
    items = [
        {
            "request_id": row.request_id,
            "preset_id": row.preset_id,
            "status": row.status,
            "image_url": image_url,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row, image_url in zip(rows, image_urls, strict=True)
    ]
    return {"items": items, "count": len(items)}
