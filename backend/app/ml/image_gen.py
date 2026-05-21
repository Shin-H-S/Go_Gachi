"""OpenAI 이미지 편집 호출 어댑터.

OpenAI 라이브러리와 직접 대화하는 유일한 파일. 다른 코드는 edit_image() 만 부르면
되고, OpenAI 의 세부 규격(모델명·크기·응답형식)은 여기 안에 숨긴다.
"""

import base64
from typing import Any

from anyio import to_thread
from openai import OpenAI

from app.core.config import settings
from app.models.schemas import ImageSize


def _client() -> OpenAI:
    """OpenAI 클라이언트를 만든다. 키가 없으면 RuntimeError(→ 503)로 명확히 실패시킨다."""
    # 로컬 개발 중 키가 없으면 서버 전체가 죽지 않고 API 호출 시점에만 명확히 실패하게 합니다.
    if not settings.openai_enabled:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _model_size_for(size: ImageSize) -> str:
    """원하는 크기의 가로세로 비율에 가장 가까운, OpenAI 가 지원하는 크기 문자열을 고른다.

    OpenAI 는 정해진 몇 가지 크기만 받으므로 근접값으로 요청하고, 정확한 픽셀은
    이후 fit_to_size() 에서 맞춘다.

    Args:
        size: 최종으로 원하는 이미지 크기.
    Returns:
        OpenAI 에 보낼 크기 문자열("1536x1024" / "1024x1536" / "1024x1024").
    """
    # OpenAI 이미지 API가 지원하는 근접 비율로 요청한 뒤, 후처리에서 정확한 픽셀로 맞춥니다.
    aspect_ratio = size.width / size.height
    if aspect_ratio > 1.15:  # 가로가 더 긴 경우
        return "1536x1024"
    if aspect_ratio < 0.87:  # 세로가 더 긴 경우
        return "1024x1536"
    return "1024x1024"  # 정사각형에 가까운 경우


def _decode_image_response(response: Any) -> bytes:
    """OpenAI 응답에서 base64 이미지 데이터를 꺼내 실제 바이트로 디코딩한다.

    Args:
        response: OpenAI images.edit 호출 결과.
    Returns:
        디코딩된 이미지 바이트(PNG).
    Raises:
        RuntimeError: 응답이 비었거나 base64 데이터가 없을 때.
    """
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
    """업로드 이미지와 프롬프트를 OpenAI 에 보내 편집·생성된 이미지를 받아온다.

    OpenAI 호출은 동기(blocking)라 시간이 오래 걸리므로, 별도 스레드에서 실행해
    그동안 서버가 다른 요청을 계속 처리할 수 있게 한다(이벤트 루프 차단 방지).

    Args:
        file_bytes: 원본 이미지 바이트.
        filename: OpenAI 에 전달할 파일명.
        content_type: 원본 MIME 타입(없으면 image/png 로 간주).
        prompt: 생성 지시문.
        size: 최종 목표 크기(요청 크기 결정에 사용).
    Returns:
        생성된 이미지 바이트(PNG).
    """

    def _call_openai() -> bytes:
        # 업로드 이미지를 기준으로 편집 생성합니다. 응답은 저장하기 쉬운 base64로 받습니다.
        response = _client().images.edit(
            model=settings.OPENAI_IMAGE_MODEL,
            image=(filename, file_bytes, content_type or "image/png"),
            prompt=prompt,
            n=1,
            size=_model_size_for(size),
            quality="medium",
        )
        return _decode_image_response(response)

    return await to_thread.run_sync(_call_openai)
