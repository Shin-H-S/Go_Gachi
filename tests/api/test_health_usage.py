import pytest

from backend.app.api import internal
from backend.app.core.config import get_settings
from backend.app.services.costs import CostSnapshot
from tests.api.helpers import client


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_internal_usage_returns_budget_keys() -> None:
    response = client.get("/api/internal/usage")
    body = response.json()

    assert response.status_code == 200
    for key in (
        "total_cost_usd",
        "generation_count",
        "cached_count",
        "budget_limit",
        "budget_alert",
        "remaining",
    ):
        assert key in body
    assert "actual_total_cost" not in body
    assert "actual_currency" not in body
    assert "cost_sync_error" not in body
    assert body["total_cost_usd"] == 0.0
    assert body["generation_count"] == 0
    assert body["cached_count"] == 0
    assert body["remaining"] == body["budget_limit"]


def test_internal_usage_includes_actual_cost_when_admin_key_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_settings = get_settings()
    monkeypatch.setattr(real_settings, "openai_admin_key", "admin-key")

    async def _fake_cost(settings):  # noqa: ANN001, ANN202
        return CostSnapshot(
            total_cost=1.59,
            currency="usd",
            start_time=1764547200,
            end_time=1764806400,
        )

    monkeypatch.setattr(internal.costs, "fetch_current_month_cost", _fake_cost)

    response = client.get("/api/internal/usage")
    body = response.json()

    assert response.status_code == 200
    assert body["total_cost_usd"] == 0.0
    assert body["actual_total_cost"] == 1.59
    assert body["actual_currency"] == "usd"
    assert body["remaining"] == body["budget_limit"]
