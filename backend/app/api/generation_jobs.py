"""비동기 이미지 생성 job API."""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from backend.app.core.auth import AuthUser, get_current_user
from backend.app.core.errors import error_detail
from backend.app.core.logging_utils import short_id
from backend.app.core.presets import Preset, PresetDetail, default_preset, get_presets
from backend.app.schemas import (
    GenerateJobCreateResponse,
    GenerateJobStatusResponse,
    GenerateRequest,
)
from backend.app.services.generation_files import new_generation_id
from backend.app.services.generation_jobs import get_job_status, register_job, run_generation_job

router = APIRouter(prefix="/api/generate/jobs", tags=["generation-jobs"])
logger = logging.getLogger(__name__)

CurrentUser = Annotated[AuthUser, Depends(get_current_user)]


def _select_preset_detail(request: GenerateRequest) -> tuple[Preset, PresetDetail]:
    presets = get_presets()
    if request.preset_id:
        preset = presets.get(request.preset_id)
        if preset is None:
            raise HTTPException(
                status_code=400,
                detail=error_detail(
                    "UNSUPPORTED_PRESET_ID",
                    f"지원하지 않는 presetId입니다: {request.preset_id}",
                ),
            )
    else:
        preset = default_preset()

    detail = (
        preset.find_detail(request.detail_type) if request.detail_type else preset.default_detail()
    )
    if detail is None:
        raise HTTPException(
            status_code=400,
            detail=error_detail(
                "UNSUPPORTED_DETAIL_TYPE",
                f"지원하지 않는 detailType입니다: {request.detail_type}",
            ),
        )
    return preset, detail


@router.post("", response_model=GenerateJobCreateResponse, response_model_by_alias=True)
async def create_generation_job(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
) -> GenerateJobCreateResponse:
    """이미지 생성 job을 등록하고 requestId를 즉시 반환한다."""
    preset, detail = _select_preset_detail(request)
    request_id = new_generation_id()
    register_job(request_id, user.id)
    background_tasks.add_task(
        run_generation_job,
        request_id=request_id,
        request=request,
        user_id=user.id,
    )
    logger.info(
        "generation job accepted request_id=%s preset=%s detail=%s user_id=%s",
        request_id,
        preset.id,
        detail.id,
        short_id(user.id),
    )
    return GenerateJobCreateResponse(
        requestId=request_id,
        jobId=request_id,
        status="pending",
    )


@router.get(
    "/{request_id}",
    response_model=GenerateJobStatusResponse,
    response_model_by_alias=True,
)
async def read_generation_job(
    request_id: str,
    user: CurrentUser,
) -> GenerateJobStatusResponse:
    """내 이미지 생성 job 상태를 조회한다."""
    status = await get_job_status(request_id=request_id, user_id=user.id)
    if status is None:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    return status
