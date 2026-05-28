"""OpenAI 실제 비용 조회 어댑터."""

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from backend.app.core.config import Settings


@dataclass(frozen=True)
class CostSnapshot:
    """OpenAI Costs API에서 가져온 기간별 실제 비용 요약."""

    total_cost: float
    currency: str
    start_time: int
    end_time: int


def current_month_range(now: datetime | None = None) -> tuple[int, int]:
    """현재 UTC 월의 시작 시각부터 현재 시각까지 Unix seconds 범위를 만든다."""
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    current = current.astimezone(UTC)
    month_start = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return int(month_start.timestamp()), int(current.timestamp())


async def fetch_current_month_cost(settings: Settings) -> CostSnapshot | None:
    """OpenAI Costs API로 이번 달 실제 조직 비용을 조회한다.

    `OPENAI_ADMIN_KEY`가 없으면 실제 비용 조회를 건너뛰고 None을 반환한다.
    """
    if not settings.openai_admin_key:
        return None

    start_time, end_time = current_month_range()
    params: dict[str, str | int] = {
        "start_time": start_time,
        "end_time": end_time,
        "bucket_width": "1d",
        "limit": 180,
    }
    total_cost = 0.0
    currency = "usd"

    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            response = await client.get(
                "https://api.openai.com/v1/organization/costs",
                headers={
                    "Authorization": f"Bearer {settings.openai_admin_key}",
                    "Content-Type": "application/json",
                },
                params=params,
            )

            try:
                payload = response.json()
            except ValueError as exc:
                raise ValueError("OpenAI 비용 API 응답을 해석하지 못했습니다.") from exc

            if response.status_code >= 400:
                message = payload.get("error", {}).get(
                    "message",
                    "OpenAI 비용 API 호출에 실패했습니다.",
                )
                raise ValueError(message)

            for bucket in payload.get("data", []):
                for result in bucket.get("results", []):
                    amount = result.get("amount", {})
                    if amount.get("currency"):
                        currency = str(amount["currency"])
                    total_cost += float(amount.get("value", 0.0))

            next_page = payload.get("next_page")
            if not payload.get("has_more") or not next_page:
                break
            params["page"] = str(next_page)

    return CostSnapshot(
        total_cost=total_cost,
        currency=currency,
        start_time=start_time,
        end_time=end_time,
    )
