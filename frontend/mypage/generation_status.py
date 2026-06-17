from datetime import UTC, datetime, timedelta

from frontend.services.api_client import to_backend_asset_url

IN_PROGRESS_STATUSES = {"pending", "processing"}
FINISHED_STATUSES = {"cached", "completed", "done", "failed", "success"}
STALE_IN_PROGRESS_AFTER = timedelta(minutes=5)


def is_generation_in_progress(status: str) -> bool:
    normalized = status.strip().lower()
    return normalized in IN_PROGRESS_STATUSES or normalized not in FINISHED_STATUSES


def _parse_created_at(value: object) -> datetime | None:
    raw_value = str(value or "").strip()
    if not raw_value:
        return None
    if raw_value.endswith("Z"):
        raw_value = f"{raw_value[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def is_stale_in_progress(status: str, created_at: object) -> bool:
    if status.strip().lower() not in IN_PROGRESS_STATUSES:
        return False
    parsed_created_at = _parse_created_at(created_at)
    if parsed_created_at is None:
        return False
    return datetime.now(UTC) - parsed_created_at > STALE_IN_PROGRESS_AFTER


def is_generation_waiting_for_image(item: dict) -> bool:
    if to_backend_asset_url(item.get("image_url")):
        return False
    status = str(item.get("status") or "")
    if status.strip().lower() not in IN_PROGRESS_STATUSES:
        return False
    return not is_stale_in_progress(status, item.get("created_at"))


def has_generation_waiting_for_image(items: list[dict]) -> bool:
    return any(is_generation_waiting_for_image(item) for item in items)


def generation_status_badge(status: str, created_at: object) -> tuple[str, str]:
    """마이페이지 작업 카드에 표시할 상태 라벨과 CSS 상태값을 반환한다."""
    normalized = status.strip().lower()
    if is_stale_in_progress(status, created_at):
        return "시간초과", "stale"
    if normalized in IN_PROGRESS_STATUSES or normalized not in FINISHED_STATUSES:
        return "생성중", "progress"
    if normalized == "failed":
        return "실패", "failed"
    if normalized == "cached":
        return "완료", "cached"
    return "완료", "success"
