"""HTTP routes for the backend API."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from app.core.config import settings
from app.models.schemas import AdGenerationInput, GeneratedAsset, HealthResponse, Placement
from app.services.pipeline import generate_ad_asset


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        openai_enabled=settings.openai_enabled,
    )


@router.post("/generate", response_model=GeneratedAsset, status_code=status.HTTP_201_CREATED)
async def generate(
    image: UploadFile = File(...),
    industry: str = Form(...),
    mood: str = Form(...),
    ad_type: str = Form(...),
    objective: str = Form(...),
    placement: Placement = Form(Placement.INSTAGRAM_FEED),
    brand_name: str | None = Form(None),
    target_audience: str | None = Form(None),
    key_message: str | None = Form(None),
    offer: str | None = Form(None),
    custom_width: int | None = Form(None),
    custom_height: int | None = Form(None),
) -> GeneratedAsset:
    try:
        # multipart/form-data 입력값을 내부 파이프라인에서 쓰는 Pydantic 모델로 정리합니다.
        ad_input = AdGenerationInput(
            industry=industry,
            mood=mood,
            ad_type=ad_type,
            objective=objective,
            placement=placement,
            brand_name=brand_name,
            target_audience=target_audience,
            key_message=key_message,
            offer=offer,
            custom_width=custom_width,
            custom_height=custom_height,
        )
        # 실제 이미지 생성 흐름은 service 레이어에 위임해 라우터는 HTTP 처리만 맡습니다.
        return await generate_ad_asset(image, ad_input)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
