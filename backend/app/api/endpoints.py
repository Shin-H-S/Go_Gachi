"""API 라우트 (/health, /generate)."""

import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import crud
from app.db.database import get_db
from app.ml import text_gen
from app.models.schemas import AdPurpose, GenerateResponse, Industry, Mood, OutputType
from app.storage import files

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """서버가 살아있는지 확인한다.

    Args:
        없음.
    Returns:
        {"status": "ok"} 형태의 dict.
    """
    return {"status": "ok"}


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    image: UploadFile = File(..., description="상품 사진"),
    industry: Industry = Form(...),
    store_name: str = Form(...),
    ad_purpose: AdPurpose | None = Form(None),
    mood: Mood | None = Form(None),
    output_type: OutputType | None = Form(None),
    price: str | None = Form(None),
    contact: str | None = Form(None),
    db: Session = Depends(get_db),
) -> GenerateResponse:
    """사진과 매장정보를 받아 광고 문구/이미지를 생성하고 DB에 기록한다.

    Args:
        image: 업로드된 상품 사진.
        industry: 업종(선택형).
        store_name: 매장명.
        ad_purpose: 광고 목적(선택).
        mood: 분위기(선택).
        output_type: 출력 용도(선택).
        price: 가격(선택).
        contact: 연락처(선택).
        db: DB 세션(의존성 주입).
    Returns:
        생성 결과(GenerateResponse): session_id, 문구, 해시태그, 이미지 경로, 소요시간.
    """
    # 0) 크기 1차 검증 (image.size 가 있으면 미리, 실제 검증은 save_upload 에서 바이트로) — 잘못되면 400
    if image.size is not None and image.size > files.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="파일이 너무 큽니다 (최대 10MB).")

    start = time.perf_counter()

    # 1) 업로드 사진 저장
    upload_path = await files.save_upload(image)

    # 2) 광고 문구 생성 (현재는 더미, 추후 OpenAI 연동)
    text = await text_gen.generate_ad_copy(
        store_name=store_name,
        industry=industry.value,
        ad_purpose=ad_purpose.value if ad_purpose else None,
        mood=mood.value if mood else None,
        output_type=output_type.value if output_type else None,
        price=price,
        contact=contact,
    )

    # 3) 생성 기록을 DB에 저장 (이미지 생성은 다음 단계 — 지금은 원본 경로만)
    gen = crud.create_generation(
        db,
        original_image_path=str(upload_path),
        ad_copy=text["ad_copy"],
    )

    return GenerateResponse(
        session_id=gen.session_id,
        ad_copy=gen.ad_copy or text["ad_copy"],
        hashtags=text["hashtags"],
        original_image_url=f"/uploads/{upload_path.name}",
        generated_image_url=None,  # 이미지 생성 연동 후 채워짐 (팀장님 OpenAI)
        elapsed_time=round(time.perf_counter() - start, 3),
    )
