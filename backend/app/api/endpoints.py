"""백엔드 API 라우트 정의 (/health, /generate).

이 파일은 'HTTP 창구' 역할만 한다. 즉 요청을 받아 입력을 정리하고,
실제 광고 생성 작업은 service 레이어(pipeline)에 넘긴 뒤, 결과나 오류를
적절한 HTTP 상태코드로 변환해 돌려준다. 무거운 로직은 여기 두지 않는다.
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from app.core.config import settings
from app.models.schemas import (
    AdGenerationInput,
    GeneratedAsset,
    HealthResponse,
    Placement,
)
from app.services.pipeline import create_ad

# 이 라우터에 등록한 경로들은 main.py 에서 /api/v1 prefix 와 함께 앱에 붙는다.
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """서버가 살아있는지, OpenAI 키가 설정됐는지 확인하는 헬스체크.

    배포 모니터링이나 프론트 연결 확인에 쓴다. 외부 호출(OpenAI 등)은 하지 않아
    빠르게 응답한다.

    Returns:
        HealthResponse: 상태("ok"), 프로젝트명, 실행환경, OpenAI 키 설정 여부.
    """
    return HealthResponse(
        status="ok",
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        # 실제 키 값은 노출하지 않고 '설정됐는지(True/False)'만 알려준다.
        openai_enabled=settings.openai_enabled,
    )


@router.post(
    "/generate", response_model=GeneratedAsset, status_code=status.HTTP_201_CREATED
)
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
    """사진과 광고 정보를 받아 광고 이미지 1장을 생성한다.

    프론트엔드는 multipart/form-data 로 사진(image)과 선택값들을 보낸다.
    각 폼 값은 검증 후 AdGenerationInput 으로 묶여 파이프라인에 전달된다.

    Args:
        image: 업로드된 원본 사진(필수).
        industry: 업종(예: "음식점").
        mood: 분위기(예: "깔끔한").
        ad_type: 광고 종류.
        objective: 광고 목적(예: "신규 오픈 홍보").
        placement: 게시 위치. 출력 이미지 크기를 결정한다(기본: 인스타 피드 1:1).
        brand_name: 상호명(선택).
        target_audience: 타깃 고객(선택).
        key_message: 핵심 메시지(선택).
        offer: 할인·혜택 문구(선택).
        custom_width: 사용자 지정 가로 픽셀(placement=custom 일 때 사용).
        custom_height: 사용자 지정 세로 픽셀(placement=custom 일 때 사용).
    Returns:
        GeneratedAsset: 생성 결과(요청 ID, 이미지 URL, 파일명, 크기, 사용된 프롬프트).
    Raises:
        HTTPException 400: 입력값이 잘못됨(예: 잘못된 파일 형식, custom 크기 누락).
        HTTPException 422: Pydantic 검증 실패(필드 형식/길이 위반).
        HTTPException 503: OpenAI 키 미설정 등으로 생성 기능을 쓸 수 없음.
    """
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
        return await create_ad(image, ad_input)
    # 아래 except 들은 내부에서 난 파이썬 예외를 프론트가 이해할 HTTP 상태코드로 번역한다.
    except ValueError as exc:
        # 잘못된 입력(파일 형식/용량, custom 크기 누락 등) → 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except ValidationError as exc:
        # Pydantic 필드 검증 실패(형식/길이 위반) → 422 (어느 필드가 틀렸는지 함께 전달)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.errors()
        ) from exc
    except RuntimeError as exc:
        # 생성 기능 자체를 못 씀(OpenAI 키 미설정 등) → 503
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
