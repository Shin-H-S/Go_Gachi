"""광고 생성 전체 흐름 조율(orchestration).

이 파일은 '총괄 매니저'다. 직접 일을 다 하지 않고, 검증·프롬프트·생성·저장 같은
세부 작업을 ml/storage 모듈에 순서대로 시킨 뒤 결과를 모아 돌려준다.
"""

from fastapi import UploadFile

from app.ml.image_gen import edit_image
from app.ml.image_utils import (
    fit_to_size,
    resolve_target_size,
    save_png,
    validate_upload,
)
from app.ml.text_gen import build_image_edit_prompt
from app.models.schemas import AdGenerationInput, GeneratedAsset
from app.storage.files import new_request_id, output_path, output_url, save_upload


async def generate_ad_asset(
    upload: UploadFile, ad_input: AdGenerationInput
) -> GeneratedAsset:
    """업로드 사진과 광고 입력을 받아 광고 이미지 1장을 생성한다.

    순서: 파일 읽기 → 검증 → 크기 결정 → 프롬프트 작성 → 원본 저장 →
    OpenAI 생성 → 결과를 목표 크기로 맞춤 → 저장 → 결과 정보 반환.

    Args:
        upload: 업로드된 원본 사진 파일.
        ad_input: 검증된 광고 생성 입력(업종·분위기·게시위치 등).
    Returns:
        GeneratedAsset: 요청 ID, 결과 이미지 URL/파일명, 크기, 사용한 프롬프트.
    """
    # 이 함수가 광고 생성의 전체 흐름을 조율합니다. 각 세부 작업은 ml/storage 모듈에 위임합니다.
    file_bytes = await upload.read()
    validate_upload(upload.content_type, file_bytes)

    request_id = new_request_id()
    target_size = resolve_target_size(
        ad_input.placement,
        custom_width=ad_input.custom_width,
        custom_height=ad_input.custom_height,
    )
    prompt = build_image_edit_prompt(ad_input, target_size)
    # 원본 업로드도 저장해두면 실패 분석이나 재생성 기능을 붙일 때 활용할 수 있습니다.
    save_upload(file_bytes, upload.content_type, request_id)

    generated_bytes = await edit_image(
        file_bytes=file_bytes,
        filename=upload.filename or f"{request_id}.png",
        content_type=upload.content_type,
        prompt=prompt,
        size=target_size,
    )
    final_image = fit_to_size(generated_bytes, target_size)

    path = output_path(request_id)
    save_png(final_image, path)

    # 프론트엔드는 image_url만 붙이면 결과 이미지를 미리보기 할 수 있습니다.
    return GeneratedAsset(
        request_id=request_id,
        image_url=output_url(path.name),
        filename=path.name,
        size=target_size,
        prompt=prompt,
    )
