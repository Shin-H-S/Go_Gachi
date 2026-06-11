from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import ApiUsage, Generation


async def record_usage(
    db: AsyncSession,
    *,
    request_id: str,
    image_model: str | None,
    text_model: str | None,
    image_cost_usd: float,
    text_cost_usd: float,
    cached: bool,
) -> ApiUsage:
    cost_usd = round(image_cost_usd + text_cost_usd, 6)
    usage = ApiUsage(
        request_id=request_id,
        provider="openai",
        image_model=image_model,
        text_model=text_model,
        image_cost_usd=image_cost_usd,
        text_cost_usd=text_cost_usd,
        cost_usd=cost_usd,
        cached=cached,
    )
    db.add(usage)
    await db.flush()
    return usage


async def usage_summary(db: AsyncSession) -> dict[str, float | int]:
    total_result = await db.execute(select(func.coalesce(func.sum(ApiUsage.cost_usd), 0.0)))
    generation_result = await db.execute(select(func.count()).select_from(Generation))
    cached_result = await db.execute(
        select(func.count()).select_from(ApiUsage).where(ApiUsage.cached.is_(True))
    )
    total_cost = float(total_result.scalar_one())
    return {
        "total_cost_usd": total_cost,
        "generation_count": int(generation_result.scalar_one()),
        "cached_count": int(cached_result.scalar_one()),
    }
