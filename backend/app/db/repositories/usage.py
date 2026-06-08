from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import ApiUsage, Generation


async def record_usage(
    db: AsyncSession,
    *,
    request_id: str,
    model: str,
    operation: str,
    estimated_cost: float,
    cached: bool,
) -> ApiUsage:
    usage = ApiUsage(
        request_id=request_id,
        provider="openai",
        model=model,
        operation=operation,
        estimated_cost=estimated_cost,
        cached=cached,
    )
    db.add(usage)
    await db.flush()
    return usage


async def usage_summary(db: AsyncSession) -> dict[str, float | int]:
    total_result = await db.execute(select(func.coalesce(func.sum(ApiUsage.estimated_cost), 0.0)))
    generation_result = await db.execute(select(func.count()).select_from(Generation))
    cached_result = await db.execute(
        select(func.count()).select_from(ApiUsage).where(ApiUsage.cached.is_(True))
    )
    return {
        "total_estimated_cost": float(total_result.scalar_one()),
        "generation_count": int(generation_result.scalar_one()),
        "cached_count": int(cached_result.scalar_one()),
    }
