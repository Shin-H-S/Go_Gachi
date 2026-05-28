"""내부 모니터링용 라우트.

데모 중 OpenAI 사용량/예산 잔여를 확인하기 위한 비공개 엔드포인트를 모은다.
사용자 화면에 노출하지 않으며, 인증/권한은 이번 범위에서 다루지 않는다.
"""

from fastapi import APIRouter

from backend.app.core.config import get_settings
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.services import costs

router = APIRouter(prefix="/api/internal", tags=["internal"])


@router.get("/usage")
async def get_usage() -> dict[str, object]:
    """내부 모니터링용 OpenAI 사용량과 예산 상태를 반환한다.

    `OPENAI_ADMIN_KEY`가 있으면 OpenAI Costs API의 실제 월간 비용을 함께 포함한다.
    키가 없으면 actual_* 필드는 응답에서 생략되고 앱 내부 추정 비용만 노출한다.

    Returns:
        dict: 앱 내부 추정 비용, 생성/캐시 수, 예산 정보. (admin key 있을 때만) 실제 조직 비용.
    """
    settings = get_settings()
    async with async_session_scope() as db:
        summary = await crud.usage_summary(db)

    estimated_total = float(summary["total_estimated_cost"])
    response: dict[str, object] = {
        **summary,
        "budget_limit": settings.openai_budget_limit_usd,
        "budget_alert": settings.openai_budget_alert_usd,
        # remaining은 항상 우리 앱 내부 추정 기준으로만 계산한다(조직 전체 비용 섞지 않음).
        "remaining": max(settings.openai_budget_limit_usd - estimated_total, 0.0),
    }

    # admin key가 없으면 Costs API 시도조차 안 한다 → 응답도 단순하게 유지.
    if not settings.openai_admin_key:
        return response

    try:
        actual_cost = await costs.fetch_current_month_cost(settings)
    except ValueError as exc:
        response["actual_total_cost"] = None
        response["cost_sync_error"] = str(exc)
        return response

    if actual_cost is None:
        return response

    response["actual_total_cost"] = actual_cost.total_cost
    response["actual_currency"] = actual_cost.currency
    response["actual_period_start"] = actual_cost.start_time
    response["actual_period_end"] = actual_cost.end_time
    response["cost_sync_error"] = None
    return response
