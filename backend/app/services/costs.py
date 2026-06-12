"""OpenAI 실제 비용 조회 어댑터 + 호출별 토큰 기반 비용 계산."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

import httpx

from backend.app.core.config import Settings

# 2026-06 기준 OpenAI 단가(USD per 1M token).
# 모델·티어 단가가 바뀌면 여기만 갱신한다.
_IMAGE_INPUT_PER_TOKEN: Final[float] = 8.0 / 1_000_000
_IMAGE_OUTPUT_PER_TOKEN: Final[float] = 30.0 / 1_000_000
_TEXT_COST_BY_MODEL: Final[dict[str, tuple[float, float]]] = {
    "gpt-5": (1.25 / 1_000_000, 10.0 / 1_000_000),
    "gpt-5.4": (2.5 / 1_000_000, 15.0 / 1_000_000),
    "gpt-5.4-mini": (0.75 / 1_000_000, 4.5 / 1_000_000),
    "gpt-5.5": (5.0 / 1_000_000, 30.0 / 1_000_000),
}

# 응답에 usage가 없을 때(옛 모델 등) 사용하는 quality별 보수적 추정 단가.
_IMAGE_COST_BY_QUALITY: Final[dict[str, float]] = {
    "low": 0.011,
    "medium": 0.042,
    "high": 0.167,
}


def calculate_image_cost(usage: dict[str, object] | None, *, quality: str = "medium") -> float:
    """OpenAI 이미지 응답의 usage(토큰 수)로 실제 호출 비용을 계산한다.

    usage가 비어 있으면 quality 기반 추정 단가로 폴백한다(옛 모델·테스트 호환).
    """
    if not usage:
        return _IMAGE_COST_BY_QUALITY.get(quality, _IMAGE_COST_BY_QUALITY["medium"])

    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    cost = input_tokens * _IMAGE_INPUT_PER_TOKEN + output_tokens * _IMAGE_OUTPUT_PER_TOKEN
    if cost <= 0:
        return _IMAGE_COST_BY_QUALITY.get(quality, _IMAGE_COST_BY_QUALITY["medium"])
    return round(cost, 6)


def calculate_text_cost(usage: dict[str, object] | None, *, model: str = "gpt-5.4-mini") -> float:
    """OpenAI 텍스트(Responses API) usage로 호출 비용을 계산한다."""
    if not usage:
        return 0.0
    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    input_rate, output_rate = _TEXT_COST_BY_MODEL.get(
        model,
        _TEXT_COST_BY_MODEL["gpt-5.4-mini"],
    )
    cost = input_tokens * input_rate + output_tokens * output_rate
    return round(cost, 6)


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
