"""OpenAI image edit adapter."""

import base64
from typing import Any

from anyio import to_thread
from openai import OpenAI

from app.core.config import settings
from app.models.schemas import ImageSize


def _client() -> OpenAI:
    # 로컬 개발 중 키가 없으면 서버 전체가 죽지 않고 API 호출 시점에만 명확히 실패하게 합니다.
    if not settings.openai_enabled:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _model_size_for(size: ImageSize) -> str:
    # OpenAI 이미지 API가 지원하는 근접 비율로 요청한 뒤, 후처리에서 정확한 픽셀로 맞춥니다.
    aspect_ratio = size.width / size.height
    if aspect_ratio > 1.15:
        return "1536x1024"
    if aspect_ratio < 0.87:
        return "1024x1536"
    return "1024x1024"


def _decode_image_response(response: Any) -> bytes:
    if not response.data:
        raise RuntimeError("OpenAI returned an empty image response")

    first_image = response.data[0]
    b64_json = getattr(first_image, "b64_json", None)
    if not b64_json:
        raise RuntimeError("OpenAI image response did not include b64_json data")
    return base64.b64decode(b64_json)


async def edit_image(
    file_bytes: bytes,
    filename: str,
    content_type: str | None,
    prompt: str,
    size: ImageSize,
) -> bytes:
    def _call_openai() -> bytes:
        # 업로드 이미지를 기준으로 편집 생성합니다. 응답은 저장하기 쉬운 base64로 받습니다.
        response = _client().images.edit(
            model=settings.OPENAI_IMAGE_MODEL,
            image=(filename, file_bytes, content_type or "image/png"),
            prompt=prompt,
            n=1,
            size=_model_size_for(size),
            quality="medium",
            response_format="b64_json",
        )
        return _decode_image_response(response)

    return await to_thread.run_sync(_call_openai)
