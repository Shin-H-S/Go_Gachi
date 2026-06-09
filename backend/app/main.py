"""Cloud Run에서 실행되는 FastAPI 진입점."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from backend.app.api.auth import router as auth_router
from backend.app.api.internal import router as internal_router
from backend.app.api.middlewares import AccessLogMiddleware, RequestIDMiddleware
from backend.app.core.auth import AuthUser, get_optional_user
from backend.app.core.config import get_settings
from backend.app.core.logging_config import setup_logging
from backend.app.core.logging_utils import short_id
from backend.app.core.presets import default_preset, get_presets
from backend.app.schemas import ConfigResponse, CopyResponse, GenerateRequest, GenerateResponse
from backend.app.services.copywriting import build_ad_copy
from backend.app.services.image_edit import edit_image

logger = logging.getLogger(__name__)
IMAGE_GENERATION_UNAVAILABLE_MESSAGE = (
    "이미지 생성 서비스에 일시적 문제가 있어요. 잠시 후 다시 시도해주세요."
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """앱 시작·종료 훅. 스키마는 Alembic 마이그레이션이 관리하므로 여기서 생성하지 않는다."""
    setup_logging(get_settings().app_env)
    yield


app = FastAPI(title="Cafe Ad Maker V1", version="0.1.0", lifespan=lifespan)

# add_middleware는 역순으로 실행되므로 RequestIDMiddleware를 나중에 등록한다.
app.add_middleware(AccessLogMiddleware)
app.add_middleware(RequestIDMiddleware)

# 인증 라우트(/api/auth/me 등)는 환경과 무관하게 항상 등록한다.
app.include_router(auth_router)

# production에서는 내부 모니터링 라우터를 아예 등록하지 않는다. 로컬/dev에선 그대로 열림.
# 운영에서도 사용량을 봐야 한다면 별도 토큰 인증 라우터로 교체하면 됨.
if get_settings().app_env != "production":
    app.include_router(internal_router)

# 생성된 이미지를 /outputs/... 경로로 프론트에 내려주기 위해 outputs 폴더를 정적 파일로 노출한다.
# 운영(Cloud Run) 환경에서는 컨테이너 디스크가 휘발성이므로 추후 GCS URL로 대체하는 것이 권장된다.
_static_output_dir = get_settings().output_dir
_static_output_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/outputs",
    StaticFiles(directory=str(_static_output_dir)),
    name="outputs",
)

_static_upload_dir = get_settings().upload_dir
_static_upload_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/uploads",
    StaticFiles(directory=str(_static_upload_dir)),
    name="uploads",
)


@app.get("/")
async def root() -> dict[str, str]:
    # Cloud Run 기본 URL로 접속했을 때 서비스가 살아있는지 빠르게 확인한다.
    return {"service": "Cafe Ad Maker V1", "status": "ok"}


@app.get("/api/health")
async def health() -> dict[str, str]:
    # 로드밸런서/스모크 테스트용 최소 헬스체크. 외부 API는 호출하지 않는다.
    return {"status": "ok"}


@app.get("/api/ready")
async def ready() -> dict[str, str | int]:
    # 런타임 설정과 프리셋 로딩 상태를 함께 확인해 배포 준비 여부를 판단한다.
    settings = get_settings()
    presets = get_presets()
    return {
        "status": "ready",
        "env": settings.app_env,
        "provider": settings.image_provider,
        "presets": len(presets),
    }


@app.get("/api/config", response_model=ConfigResponse, response_model_by_alias=True)
async def config() -> ConfigResponse:
    # 프론트는 이 응답으로 사용 가능한 광고 규격과 현재 provider를 구성한다.
    settings = get_settings()
    return ConfigResponse(
        presets=list(get_presets().values()),
        provider=settings.image_provider,
        maxUploadBytes=settings.max_upload_bytes,
    )


@app.post("/api/generate", response_model=GenerateResponse, response_model_by_alias=True)
async def generate(
    request: GenerateRequest,
    user: AuthUser | None = Depends(get_optional_user),
) -> GenerateResponse:
    # presetId가 없으면 기본 프리셋을 쓰고, 잘못된 값은 연동 오류를 빨리 찾도록 400으로 돌려준다.
    settings = get_settings()
    presets = get_presets()
    if request.preset_id:
        preset = presets.get(request.preset_id)
        if preset is None:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 presetId입니다: {request.preset_id}",
            )
    else:
        preset = default_preset()

    detail = (
        preset.find_detail(request.detail_type) if request.detail_type else preset.default_detail()
    )
    if detail is None:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 detailType입니다: {request.detail_type}",
        )

    logger.info(
        "generate started preset=%s detail=%s user_id=%s",
        preset.id,
        detail.id,
        short_id(user.id) if user else "-",
    )

    ad_copy = None
    copy_info = None
    if request.text_overlay_enabled:
        # V3 텍스트 합성 전 단계: 사용자 요청을 광고 문구 구조로 먼저 정리한다.
        copy_source = (request.user_copy or "").strip() or request.user_prompt
        ad_copy = build_ad_copy(copy_source, request.copy_mode)
        copy_info = CopyResponse(**ad_copy.model_dump())

    try:
        # 이미지 검증, mock/openai 분기, 외부 API 호출은 service 계층에 위임한다.
        result = await edit_image(
            image_data_url=request.image_data_url,
            preset=preset,
            detail=detail,
            user_prompt=request.user_prompt,
            target_width=request.target_width,
            target_height=request.target_height,
            resize_mode=request.resize_mode,
            settings=settings,
            # 로그인했으면 생성 기록에 소유자로 남긴다(비로그인이면 None).
            user_id=user.id if user else None,
            user_copy=request.user_copy,
            logo_data_url=request.logo_data_url,
            logo_position=request.logo_position,
            text_copy=ad_copy,
        )
    except ValueError as exc:
        # 사용자 입력 문제는 프론트가 처리할 수 있게 400으로 돌려준다.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        # 서버 설정/외부 이미지 API 문제는 내부 로그에만 원인을 남기고 사용자 메시지는 일반화한다.
        logger.exception("image generation failed")
        raise HTTPException(
            status_code=503,
            detail=IMAGE_GENERATION_UNAVAILABLE_MESSAGE,
        ) from exc

    logger.debug(
        "generate finished provider=%s preset=%s detail=%s",
        result["provider"] or settings.image_provider,
        preset.id,
        detail.id,
    )

    return GenerateResponse(
        imageDataUrl=result["image_data_url"],
        imageUrl=result.get("image_url"),
        provider=result["provider"] or settings.image_provider,
        preset=preset,
        copy=copy_info,
        note=result["note"],
        # production에서는 내부 프롬프트 노출을 막고, local/dev에서는 디버깅용으로 유지한다.
        prompt=result["prompt"] if settings.app_env != "production" else None,
    )
