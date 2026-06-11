"""OpenAI 이미지 편집 API 호출과 응답 파싱."""

import logging
import time

import httpx

from backend.app.core.config import Settings
from backend.app.core.errors import ServiceError
from backend.app.services.image_types import UploadedImage

logger = logging.getLogger(__name__)


def _extract_b64_json(payload: object) -> str:
    """OpenAI 이미지 응답에서 결과 base64를 안전하게 꺼낸다."""
    if not isinstance(payload, dict):
        raise ServiceError(
            "IMAGE_API_RESPONSE_INVALID",
            "이미지 API 응답 형식이 올바르지 않습니다.",
        )

    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise ServiceError("IMAGE_API_RESULT_EMPTY", "이미지 API 응답에 결과 이미지가 없습니다.")

    first_item = data[0]
    if not isinstance(first_item, dict):
        raise ServiceError(
            "IMAGE_API_RESPONSE_INVALID",
            "이미지 API 응답 형식이 올바르지 않습니다.",
        )

    b64_json = first_item.get("b64_json")
    if not isinstance(b64_json, str) or not b64_json.strip():
        raise ServiceError("IMAGE_API_RESULT_EMPTY", "이미지 API 응답에 결과 이미지가 없습니다.")

    return b64_json


async def call_openai_edit(
    *,
    uploaded: UploadedImage,
    reference_images: list[UploadedImage] | None = None,
    api_size: str,
    prompt: str,
    settings: Settings,
) -> tuple[str, dict[str, object]]:
    """OpenAI Images Edit API를 호출하고 (결과 base64, usage dict)을 돌려준다.

    usage는 토큰 기반 비용 계산용. 응답에 없으면 빈 dict.
    """
    start = time.perf_counter()
    images = [uploaded, *(reference_images or [])]
    files: dict[str, tuple[str, bytes, str]] | list[tuple[str, tuple[str, bytes, str]]]
    if len(images) == 1:
        files = {
            "image": (
                f"menu.{uploaded.extension}",
                uploaded.content,
                uploaded.mime_type,
            )
        }
    else:
        # OpenAI Images Edit API는 다중 reference 이미지를 image[] multipart 필드로 받는다.
        files = [
            (
                "image[]",
                (
                    f"image-{index}.{image.extension}",
                    image.content,
                    image.mime_type,
                ),
            )
            for index, image in enumerate(images, start=1)
        ]

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # OpenAI Images Edit API는 이미지 파일을 multipart/form-data로 받는다.
            response = await client.post(
                "https://api.openai.com/v1/images/edits",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                data={
                    "model": settings.openai_image_model,
                    "prompt": prompt,
                    "size": api_size,
                    "quality": settings.openai_image_quality,
                    "output_format": "png",
                },
                files=files,
            )
    except httpx.TimeoutException as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.warning(
            "OpenAI image edit timed out model=%s image_count=%s took=%.1fms error=%s",
            settings.openai_image_model,
            len(images),
            elapsed_ms,
            type(exc).__name__,
        )
        raise ServiceError("IMAGE_API_TIMEOUT", "이미지 API 응답 시간이 초과되었습니다.") from exc
    except httpx.HTTPError as exc:
        # 네트워크 실패·타임아웃·DNS 등은 사용자 잘못이 아니라 외부 의존성 문제다.
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.warning(
            "OpenAI image edit connection failed model=%s image_count=%s took=%.1fms error=%s",
            settings.openai_image_model,
            len(images),
            elapsed_ms,
            type(exc).__name__,
        )
        raise ServiceError(
            "IMAGE_API_CONNECTION_FAILED",
            "이미지 API에 연결하지 못했습니다.",
        ) from exc

    elapsed_ms = (time.perf_counter() - start) * 1000
    response_headers = getattr(response, "headers", {})
    openai_request_id = response_headers.get("x-request-id") if response_headers else None

    try:
        # 오류 응답도 JSON으로 오는 경우가 많아 먼저 payload로 통일한다.
        payload = response.json()
    except ValueError as exc:
        raise ServiceError(
            "IMAGE_API_RESPONSE_PARSE_FAILED",
            "이미지 API 응답을 해석하지 못했습니다.",
        ) from exc

    if response.status_code >= 400:
        raw_message = "이미지 생성에 실패했습니다."
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                raw_message = str(error.get("message") or raw_message)
        logger.warning(
            "OpenAI image edit failed status=%s model=%s image_count=%s took=%.1fms "
            "openai_request_id=%s message=%s",
            response.status_code,
            settings.openai_image_model,
            len(images),
            elapsed_ms,
            openai_request_id or "-",
            raw_message,
        )
        raise ServiceError("IMAGE_API_REJECTED", "이미지 생성 요청이 외부 API에서 거절되었습니다.")

    usage = payload.get("usage") if isinstance(payload, dict) else None
    if not isinstance(usage, dict):
        usage = {}
    logger.info(
        "OpenAI image edit finished status=%s model=%s image_count=%s took=%.1fms "
        "openai_request_id=%s input_tokens=%s output_tokens=%s",
        response.status_code,
        settings.openai_image_model,
        len(images),
        elapsed_ms,
        openai_request_id or "-",
        usage.get("input_tokens", "-"),
        usage.get("output_tokens", "-"),
    )
    return _extract_b64_json(payload), usage
