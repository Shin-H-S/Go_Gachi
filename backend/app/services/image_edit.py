"""이미지 입력 검증과 OpenAI 이미지 편집 호출."""

import asyncio
import base64
import binascii
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx

from backend.app.core.config import Settings
from backend.app.core.presets import Preset
from backend.app.core.prompts import PROMPT_VERSION, build_prompt
from backend.app.db import crud
from backend.app.db.database import async_session_scope

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


async def _file_to_data_url(path: Path) -> str:
    """저장된 PNG 파일을 base64 data URL로 인코딩한다(캐시 hit 응답용)."""
    content = await asyncio.to_thread(path.read_bytes)
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:image/png;base64,{encoded}"


async def _call_openai_edit(
    *,
    uploaded: UploadedImage,
    preset: Preset,
    prompt: str,
    settings: Settings,
) -> str:
    """OpenAI Images Edit API를 호출하고 결과 base64 문자열을 돌려준다.

    Args:
        uploaded: 검증된 업로드 이미지.
        preset: 광고 규격 정보.
        prompt: 모델에 보낼 최종 프롬프트.
        settings: 런타임 설정.
    Returns:
        결과 PNG의 base64 문자열(헤더 없음).
    """
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
    return b64_json


async def edit_image(
    *,
    image_data_url: str,
    preset: Preset,
    feedback: str,
    settings: Settings,
) -> dict[str, str | None]:
    """설정된 provider에 따라 mock 반환 또는 OpenAI 이미지 편집을 수행한다.

    openai 모드에서는 동일 입력(이미지+프리셋+feedback+모델+프롬프트 버전)이면
    DB 캐시를 재사용하고, 실패해도 DB에 흔적을 남긴다. mock 모드는 DB·캐시 모두
    건너뛰어 로컬 플로우만 검증한다.
    """
    # provider와 무관하게 먼저 입력 이미지를 검증해 프론트 오류를 빠르게 돌려준다.
    uploaded = parse_image(image_data_url, settings.max_upload_bytes)

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

    prompt = build_prompt(preset, feedback)
    image_hash = crud.image_sha256(uploaded.content)
    instruction_hash = crud.instruction_sha256(feedback)
    model = settings.openai_image_model
    prompt_version = PROMPT_VERSION

    # 1) 캐시 조회. 세션을 빨리 닫고 필요한 컬럼은 dict로 스냅샷한다
    # (commit으로 expire되면 detached 상태에서 다시 접근 못 함).
    async with async_session_scope() as db:
        cached_row = await crud.find_cached_generation(
            db,
            image_hash=image_hash,
            preset_id=preset.id,
            instruction_hash=instruction_hash,
            model=model,
            prompt_version=prompt_version,
        )
        cached_snapshot: dict[str, str | None] | None
        if cached_row is None:
            cached_snapshot = None
        else:
            cached_snapshot = {
                "image_hash": cached_row.image_hash,
                "preset_id": cached_row.preset_id,
                "instruction_hash": cached_row.instruction_hash,
                "prompt_version": cached_row.prompt_version,
                "model": cached_row.model,
                "original_path": cached_row.original_path,
                "output_path": cached_row.output_path,
                "image_url": cached_row.image_url,
                "prompt": cached_row.prompt,
            }

    # 2) 캐시 hit: 파일이 실제로 읽혀서 응답 만들 준비가 끝난 뒤에만 DB에 기록한다.
    if cached_snapshot is not None and cached_snapshot["output_path"]:
        cached_path = Path(cached_snapshot["output_path"])
        if await asyncio.to_thread(cached_path.exists):
            # 파일 읽기 성공 → 그 다음에야 cached 기록·사용량을 남긴다(부분 실패 방지).
            image_data_url = await _file_to_data_url(cached_path)
            request_id = uuid.uuid4().hex
            async with async_session_scope() as db:
                await crud.create_cached_generation(
                    db,
                    request_id=request_id,
                    image_hash=cached_snapshot["image_hash"],
                    preset_id=cached_snapshot["preset_id"],
                    instruction_hash=cached_snapshot["instruction_hash"],
                    prompt_version=cached_snapshot["prompt_version"],
                    model=cached_snapshot["model"],
                    original_path=cached_snapshot["original_path"],
                    output_path=cached_snapshot["output_path"],
                    image_url=cached_snapshot["image_url"],
                    prompt=cached_snapshot["prompt"],
                )
                await crud.record_usage(
                    db,
                    request_id=request_id,
                    model=model,
                    operation="image_edit",
                    estimated_cost=0.0,
                    cached=True,
                )
            return {
                "image_data_url": image_data_url,
                "provider": "openai",
                "note": "캐시된 결과 재사용",
                "prompt": cached_snapshot["prompt"],
                "image_url": cached_snapshot["image_url"],
            }
        # 파일이 사라졌으면 캐시 미스로 떨어져 OpenAI 호출 분기로 이어진다.

    # 2) 캐시 미스: pending 행 먼저 만든 뒤 OpenAI 호출. 실패해도 흔적 남기기 위함.
    request_id = uuid.uuid4().hex
    await asyncio.to_thread(settings.output_dir.mkdir, parents=True, exist_ok=True)
    output_path = settings.output_dir / f"{request_id}.png"

    async with async_session_scope() as db:
        await crud.create_pending_generation(
            db,
            request_id=request_id,
            image_hash=image_hash,
            preset_id=preset.id,
            instruction_hash=instruction_hash,
            prompt_version=prompt_version,
            model=model,
            original_path=None,
            prompt=prompt,
        )

    try:
        b64_json = await _call_openai_edit(
            uploaded=uploaded,
            preset=preset,
            prompt=prompt,
            settings=settings,
        )
        decoded = base64.b64decode(b64_json)
        await asyncio.to_thread(output_path.write_bytes, decoded)
    except Exception as exc:
        # OpenAI 호출/응답 디코딩/파일 저장 중 하나라도 실패하면 failed로 남긴다.
        async with async_session_scope() as db:
            await crud.mark_generation_failed(
                db,
                request_id=request_id,
                error_message=str(exc)[:500],
            )
            await crud.record_usage(
                db,
                request_id=request_id,
                model=model,
                operation="image_edit",
                estimated_cost=0.0,
                cached=False,
            )
        raise

    # 3) 성공: 파일로 저장 → DB success로 갱신 → 사용량 기록.
    async with async_session_scope() as db:
        await crud.mark_generation_success(
            db,
            request_id=request_id,
            output_path=str(output_path),
            image_url=None,
        )
        await crud.record_usage(
            db,
            request_id=request_id,
            model=model,
            operation="image_edit",
            estimated_cost=settings.openai_image_edit_estimated_cost_usd,
            cached=False,
        )

    # 프론트가 별도 파일 저장 없이 바로 미리보기할 수 있도록 data URL로 반환한다.
    return {
        "image_data_url": f"data:image/png;base64,{b64_json}",
        "provider": "openai",
        "note": None,
        "prompt": prompt,
    }
