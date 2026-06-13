"""비동기 이미지 생성 job 실행과 상태 조회."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from backend.app.core.config import get_settings
from backend.app.core.errors import ServiceError
from backend.app.core.logging_utils import short_id
from backend.app.core.presets import default_preset, get_presets
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.db.models import Generation
from backend.app.schemas import GenerateJobStatusResponse, GenerateRequest
from backend.app.services.costs import calculate_text_cost
from backend.app.services.image_edit import edit_image
from backend.app.services.openai_copy import generate_ad_copy
from backend.app.services.storage_url import output_url_if_exists_async, upload_url_if_exists_async

logger = logging.getLogger(__name__)

STALE_AFTER = timedelta(minutes=5)
KEEP_DONE_JOBS_FOR = timedelta(minutes=20)


@dataclass
class TransientJob:
    user_id: str
    status: str
    error: str | None
    created_at: datetime
    updated_at: datetime


_jobs: dict[str, TransientJob] = {}


def register_job(request_id: str, user_id: str) -> None:
    """DB row 생성 전까지 조회할 수 있도록 메모리에 job 상태를 기록한다."""
    cleanup_jobs()
    now = datetime.now(UTC)
    _jobs[request_id] = TransientJob(
        user_id=user_id,
        status="pending",
        error=None,
        created_at=now,
        updated_at=now,
    )


def _set_job_status(request_id: str, status: str, error: str | None = None) -> None:
    job = _jobs.get(request_id)
    if job is None:
        return
    job.status = status
    job.error = error
    job.updated_at = datetime.now(UTC)


def _is_stale(value: datetime | None) -> bool:
    if value is None:
        return False
    checked = value if value.tzinfo else value.replace(tzinfo=UTC)
    return datetime.now(UTC) - checked > STALE_AFTER


def cleanup_jobs() -> None:
    """완료/실패 후 20분 지난 메모리 job을 정리한다."""
    cutoff = datetime.now(UTC) - KEEP_DONE_JOBS_FOR
    expired = [
        request_id
        for request_id, job in _jobs.items()
        if job.status in {"done", "failed"} and job.updated_at < cutoff
    ]
    for request_id in expired:
        _jobs.pop(request_id, None)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


async def run_generation_job(
    *,
    request_id: str,
    request: GenerateRequest,
    user_id: str,
) -> None:
    """백그라운드에서 기존 생성 파이프라인을 실행한다."""
    _set_job_status(request_id, "processing")
    settings = get_settings()
    presets = get_presets()
    preset = presets.get(request.preset_id) if request.preset_id else default_preset()
    detail = (
        preset.find_detail(request.detail_type) if request.detail_type else preset.default_detail()
    )

    try:
        ad_copy = None
        text_cost_usd = 0.0
        if request.ad_copy_enabled:
            copy_result = await generate_ad_copy(
                settings=settings,
                preset=preset,
                detail=detail,
                user_prompt=request.user_prompt,
                user_copy=request.user_copy or "",
                copy_mode=request.copy_mode,
            )
            if copy_result.used_openai:
                text_cost_usd = calculate_text_cost(
                    copy_result.usage,
                    model=settings.openai_text_model,
                )
            ad_copy = copy_result.copy

        await edit_image(
            image_data_url=request.image_data_url,
            preset=preset,
            detail=detail,
            user_prompt=request.user_prompt,
            target_width=request.target_width,
            target_height=request.target_height,
            resize_mode=request.resize_mode,
            settings=settings,
            user_id=user_id,
            user_copy=request.user_copy,
            text_copy=ad_copy,
            text_cost_usd=text_cost_usd,
            generation_id=request_id,
        )
        _set_job_status(request_id, "done")
    except Exception as exc:
        logger.exception(
            "generation job failed request_id=%s user_id=%s",
            request_id,
            short_id(user_id),
        )
        error_code = exc.code if isinstance(exc, ServiceError) else "INTERNAL_ERROR"
        _set_job_status(request_id, "failed", error_code)


async def get_job_status(
    *,
    request_id: str,
    user_id: str,
) -> GenerateJobStatusResponse | None:
    """DB row가 있으면 DB 기준, 없으면 메모리 job 기준으로 상태를 반환한다."""
    cleanup_jobs()
    async with async_session_scope() as db:
        row = await crud.get_user_generation_by_request_id(
            db,
            user_id=user_id,
            request_id=request_id,
        )

    if row is not None:
        return await _status_from_row(row)

    job = _jobs.get(request_id)
    if job is None or job.user_id != user_id:
        return None
    return _status_from_transient(request_id, job)


async def _status_from_row(row: Generation) -> GenerateJobStatusResponse:
    status = row.status
    error = row.error_message
    if status in {"pending", "processing"} and _is_stale(row.updated_at):
        status = "failed"
        error = "GENERATION_JOB_STALE"

    image_url = await output_url_if_exists_async(row.output_path)
    original_image_url = await upload_url_if_exists_async(row.original_path)
    return GenerateJobStatusResponse(
        requestId=row.request_id,
        jobId=row.request_id,
        status=status,
        imageUrl=image_url,
        originalImageUrl=original_image_url,
        error=error,
        createdAt=_iso(row.created_at),
        updatedAt=_iso(row.updated_at),
    )


def _status_from_transient(request_id: str, job: TransientJob) -> GenerateJobStatusResponse:
    status = job.status
    error = job.error
    if status in {"pending", "processing"} and _is_stale(job.updated_at):
        status = "failed"
        error = "GENERATION_JOB_STALE"

    return GenerateJobStatusResponse(
        requestId=request_id,
        jobId=request_id,
        status=status,
        imageUrl=None,
        originalImageUrl=None,
        error=error,
        createdAt=_iso(job.created_at),
        updatedAt=_iso(job.updated_at),
    )
