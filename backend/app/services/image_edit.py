"""이미지 입력 검증과 OpenAI 이미지 편집 호출."""

import base64
import binascii
import re
from dataclasses import dataclass

import httpx

from backend.app.core.config import Settings
from backend.app.core.presets import Preset
from backend.app.core.prompts import build_prompt

DATA_URL_PATTERN = re.compile(
    r"^data:(image/(?:png|jpe?g|webp));base64,([A-Za-z0-9+/=]+)$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class UploadedImage:
    """OpenAI multipart 요청에 필요한 업로드 이미지 정보."""

    mime_type: str
    content: bytes
    extension: str


def parse_image(data_url: str, max_upload_bytes: int) -> UploadedImage:
    """프론트가 보낸 data URL을 검증하고 이미지 바이트로 변환한다."""
    match = DATA_URL_PATTERN.match(data_url or "")
    if not match:
        raise ValueError("PNG, JPG, WEBP 이미지만 업로드할 수 있습니다.")

    mime_type = match.group(1).lower().replace("image/jpg", "image/jpeg")
    try:
        # validate=True로 깨진 base64가 500이 아니라 사용자 입력 오류가 되게 한다.
        content = base64.b64decode(match.group(2), validate=True)
    except binascii.Error as exc:
        raise ValueError("이미지 데이터가 올바른 base64 형식이 아닙니다.") from exc

    if not content or len(content) > max_upload_bytes:
        raise ValueError("이미지는 50MB 이하만 업로드할 수 있습니다.")

    extension = "jpg" if mime_type == "image/jpeg" else mime_type.split("/")[-1]
    return UploadedImage(mime_type=mime_type, content=content, extension=extension)


async def edit_image(
    *,
    image_data_url: str,
    preset: Preset,
    feedback: str,
    settings: Settings,
) -> dict[str, str | None]:
    """설정된 provider에 따라 mock 반환 또는 OpenAI 이미지 편집을 수행한다."""
    # provider와 무관하게 먼저 입력 이미지를 검증해 프론트 오류를 빠르게 돌려준다.
    parse_image(image_data_url, settings.max_upload_bytes)

    if settings.image_provider == "mock":
        # mock은 GCP 배포/프론트 연동 흐름만 확인할 때 사용한다.
        return {
            "image_data_url": image_data_url,
            "provider": "mock",
            "note": "OPENAI_API_KEY가 없어 원본 이미지로 로컬 흐름만 확인했습니다.",
            "prompt": None,
        }

    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

    # 실제 호출 시에는 검증된 이미지 바이트와 프롬프트가 모두 필요하다.
    uploaded = parse_image(image_data_url, settings.max_upload_bytes)
    prompt = build_prompt(preset, feedback)

    async with httpx.AsyncClient(timeout=120) as client:
        # OpenAI Images Edit API는 이미지 파일을 multipart/form-data로 받는다.
        response = await client.post(
            "https://api.openai.com/v1/images/edits",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            data={
                "model": settings.openai_image_model,
                "prompt": prompt,
                "size": preset.api_size,
                "quality": settings.openai_image_quality,
                "output_format": "png",
            },
            files={
                "image": (
                    f"menu.{uploaded.extension}",
                    uploaded.content,
                    uploaded.mime_type,
                )
            },
        )

    try:
        # 오류 응답도 JSON으로 오는 경우가 많아 먼저 payload로 통일한다.
        payload = response.json()
    except ValueError as exc:
        raise ValueError("이미지 API 응답을 해석하지 못했습니다.") from exc

    if response.status_code >= 400:
        message = payload.get("error", {}).get("message", "이미지 생성에 실패했습니다.")
        raise ValueError(message)

    b64_json = payload.get("data", [{}])[0].get("b64_json")
    if not b64_json:
        raise ValueError("이미지 API 응답에 결과 이미지가 없습니다.")

    # 프론트가 별도 파일 저장 없이 바로 미리보기할 수 있도록 data URL로 반환한다.
    return {
        "image_data_url": f"data:image/png;base64,{b64_json}",
        "provider": "openai",
        "note": None,
        "prompt": prompt,
    }
