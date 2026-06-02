"""광고 이미지 생성 전체 흐름 조립."""

import asyncio
import base64
import logging
import uuid
from datetime import datetime
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.core.presets import Preset, PresetDetail
from backend.app.core.prompts import PROMPT_VERSION, build_prompt
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.services.image_processing import normalize_for_openai, render_target_png
from backend.app.services.image_types import ResizeMode, TargetSize
from backend.app.services.image_validation import parse_image
from backend.app.services.openai_images import call_openai_edit

logger = logging.getLogger(__name__)


def _new_request_id() -> str:
    """파일 탐색기에서 시간순 정렬·가독성을 위해 `YYYYMMDD_HHMMSS_<6hex>` 형식으로 발급한다."""
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def _target_size_or_preset(
    *,
    preset: Preset,
    target_width: int | None,
    target_height: int | None,
) -> TargetSize:
    """요청 출력 크기가 없으면 프리셋 기본 크기를 사용한다."""
    if target_width is None or target_height is None:
        return TargetSize(width=preset.width, height=preset.height)
    return TargetSize(width=target_width, height=target_height)


def _feedback_with_context(
    feedback: str,
    target_size: TargetSize,
    detail: PresetDetail | None,
    resize_mode: ResizeMode,
) -> str:
    """프롬프트와 캐시 키에 최종 출력 크기를 함께 반영한다."""
    context_parts = [
        f"Target output canvas: {target_size.width}x{target_size.height}px. "
        "Compose for this final aspect ratio."
    ]
    if resize_mode == "contain":
        context_parts.append("Final resize mode: contain. Preserve the full generated image.")
    else:
        context_parts.append("Final resize mode: cover. Fill the canvas edge to edge.")
    if detail:
        context_parts.append(f"Selected detail type: {detail.id} ({detail.label}).")

    clean_feedback = (feedback or "").strip()
    if clean_feedback:
        context_parts.append(clean_feedback)
    return "\n".join(context_parts)


async def _file_to_data_url(path: Path) -> str:
    """저장된 PNG 파일을 base64 data URL로 인코딩한다(캐시 hit 응답용)."""
    content = await asyncio.to_thread(path.read_bytes)
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:image/png;base64,{encoded}"


async def edit_image(
    *,
    image_data_url: str,
    preset: Preset,
    feedback: str,
    detail: PresetDetail | None = None,
    target_width: int | None = None,
    target_height: int | None = None,
    resize_mode: ResizeMode = "cover",
    settings: Settings,
) -> dict[str, str | None]:
    """설정된 provider에 따라 mock 반환 또는 OpenAI 이미지 편집을 수행한다."""
    # provider와 무관하게 먼저 입력 이미지를 검증해 프론트 오류를 빠르게 돌려준다.
    uploaded = parse_image(image_data_url, settings.max_upload_bytes)
    target_size = _target_size_or_preset(
        preset=preset,
        target_width=target_width,
        target_height=target_height,
    )
    generation_feedback = _feedback_with_context(feedback, target_size, detail, resize_mode)

    if settings.image_provider == "mock":
        # mock은 GCP 배포/프론트 연동 흐름만 확인할 때 사용한다.
        target_png = render_target_png(uploaded.content, target_size, resize_mode)
        encoded = base64.b64encode(target_png).decode("ascii")
        return {
            "image_data_url": f"data:image/png;base64,{encoded}",
            "provider": "mock",
            "note": "OPENAI_API_KEY가 없어 선택한 규격으로 로컬 흐름만 확인했습니다.",
            "prompt": None,
        }

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

    prompt = build_prompt(preset, generation_feedback, detail)
    image_hash = crud.image_sha256(uploaded.content)
    instruction_hash = crud.instruction_sha256(generation_feedback)
    model = settings.openai_image_model
    prompt_version = PROMPT_VERSION

    # 1) 캐시 조회. 세션을 빨리 닫고 필요한 컬럼은 dict로 스냅샷한다.
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

    # 2) 캐시 hit: 파일 읽기 성공 뒤에만 cached 기록·사용량을 남긴다.
    if cached_snapshot is not None and cached_snapshot["output_path"]:
        cached_path = Path(cached_snapshot["output_path"])
        if await asyncio.to_thread(cached_path.exists):
            image_data_url = await _file_to_data_url(cached_path)
            request_id = _new_request_id()
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

    # 3) 캐시 미스: pending 행 먼저 만든 뒤 OpenAI 호출. 실패해도 흔적 남기기 위함.
    request_id = _new_request_id()
    await asyncio.to_thread(settings.upload_dir.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(settings.output_dir.mkdir, parents=True, exist_ok=True)
    original_path = settings.upload_dir / f"{request_id}.{uploaded.extension}"
    output_path = settings.output_dir / f"{request_id}.png"
    await asyncio.to_thread(original_path.write_bytes, uploaded.content)

    async with async_session_scope() as db:
        await crud.create_pending_generation(
            db,
            request_id=request_id,
            image_hash=image_hash,
            preset_id=preset.id,
            instruction_hash=instruction_hash,
            prompt_version=prompt_version,
            model=model,
            original_path=str(original_path),
            prompt=prompt,
        )

    try:
        openai_uploaded = await asyncio.to_thread(normalize_for_openai, uploaded)
        logger.info(
            "OpenAI image input prepared request_id=%s original_mime=%s "
            "original_format=%s original_mode=%s original_size=%sx%s "
            "normalized_mime=%s normalized_format=%s normalized_mode=%s "
            "normalized_size=%sx%s normalized_bytes=%s",
            request_id,
            uploaded.mime_type,
            uploaded.info.format,
            uploaded.info.mode,
            uploaded.info.width,
            uploaded.info.height,
            openai_uploaded.mime_type,
            openai_uploaded.info.format,
            openai_uploaded.info.mode,
            openai_uploaded.info.width,
            openai_uploaded.info.height,
            len(openai_uploaded.content),
        )
        b64_json = await call_openai_edit(
            uploaded=openai_uploaded,
            preset=preset,
            prompt=prompt,
            settings=settings,
        )
        # OpenAI가 응답은 했지만 결과 이미지 base64가 깨졌다면 외부 응답 처리 실패로 본다.
        decoded = base64.b64decode(b64_json, validate=True)
        target_png = await asyncio.to_thread(
            render_target_png,
            decoded,
            target_size,
            resize_mode,
        )
        await asyncio.to_thread(output_path.write_bytes, target_png)
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
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError("이미지 API 응답 이미지를 처리하지 못했습니다.") from exc

    # 4) 성공: 파일 저장 → DB success 갱신 → 사용량 기록.
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
        "image_data_url": f"data:image/png;base64,{base64.b64encode(target_png).decode('ascii')}",
        "provider": "openai",
        "note": None,
        "prompt": prompt,
    }
