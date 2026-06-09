"""광고 이미지 생성 전체 흐름 조립."""

import asyncio
import base64
import logging
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.core.logging_utils import short_id
from backend.app.core.presets import Preset, PresetDetail
from backend.app.core.prompts import PROMPT_VERSION, build_prompt
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.services.generation_files import file_to_data_url, new_generation_id
from backend.app.services.generation_inputs import target_size_or_detail, user_prompt_with_context
from backend.app.services.image_processing import normalize_for_openai, render_target_png
from backend.app.services.image_types import ResizeMode
from backend.app.services.image_validation import parse_image
from backend.app.services.openai_images import call_openai_edit
from backend.app.services.storage_url import output_url

logger = logging.getLogger(__name__)


async def edit_image(
    *,
    image_data_url: str,
    preset: Preset,
    user_prompt: str,
    detail: PresetDetail | None = None,
    target_width: int | None = None,
    target_height: int | None = None,
    resize_mode: ResizeMode = "cover",
    settings: Settings,
    user_id: str | None = None,
    user_copy: str | None = None,
    logo_data_url: str | None = None,
    logo_position: str | None = None,
) -> dict[str, str | None]:
    """설정된 provider에 따라 mock 반환 또는 OpenAI 이미지 편집을 수행한다.

    user_id가 있으면 생성 기록에 소유자로 남긴다(비로그인이면 None,
    캐시 조회 키에는 영향을 주지 않는다).
    """
    # provider와 무관하게 먼저 입력 이미지를 검증해 프론트 오류를 빠르게 돌려준다.
    uploaded = parse_image(image_data_url, settings.max_upload_bytes)
    selected_detail = detail or preset.default_detail()
    target_size = target_size_or_detail(
        detail=selected_detail,
        target_width=target_width,
        target_height=target_height,
    )
    clean_user_copy = (user_copy or "").strip() or None
    user_prompt_parts = [user_prompt]
    if clean_user_copy:
        user_prompt_parts.append(f"Ad copy to place in the image: {clean_user_copy}")
    user_prompt_for_generation = "\n".join(
        part.strip() for part in user_prompt_parts if part.strip()
    )
    generation_user_prompt = user_prompt_with_context(
        user_prompt_for_generation,
        target_size,
        selected_detail,
        resize_mode,
    )
    has_logo = bool(logo_data_url and logo_data_url.strip())
    stored_logo_position = logo_position if has_logo else None

    if settings.image_provider == "mock":
        # mock은 GCP 배포/프론트 연동 흐름만 확인할 때 사용한다.
        target_png = render_target_png(uploaded.content, target_size, resize_mode)
        encoded = base64.b64encode(target_png).decode("ascii")
        return {
            "image_data_url": f"data:image/png;base64,{encoded}",
            # mock은 파일을 저장하지 않으므로 외부에서 받을 수 있는 URL이 없다.
            "image_url": None,
            "provider": "mock",
            "note": "OPENAI_API_KEY가 없어 선택한 규격으로 로컬 흐름만 확인했습니다.",
            "prompt": None,
        }

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

    prompt = build_prompt(preset, generation_user_prompt, selected_detail)
    image_hash = crud.image_sha256(uploaded.content)
    instruction_hash = crud.instruction_sha256(generation_user_prompt)
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
            image_data_url = await file_to_data_url(cached_path)
            # DB에는 환경별 호스트를 저장하지 않고, 응답에만 /outputs/... 경로를 만든다.
            image_url = output_url(cached_path)
            generation_id = new_generation_id()
            logger.info(
                "cache hit generation_id=%s image_hash=%s preset=%s user_id=%s",
                generation_id,
                short_id(cached_snapshot["image_hash"]),
                cached_snapshot["preset_id"],
                short_id(user_id),
            )
            async with async_session_scope() as db:
                await crud.create_cached_generation(
                    db,
                    request_id=generation_id,
                    image_hash=cached_snapshot["image_hash"],
                    preset_id=cached_snapshot["preset_id"],
                    instruction_hash=cached_snapshot["instruction_hash"],
                    prompt_version=cached_snapshot["prompt_version"],
                    model=cached_snapshot["model"],
                    original_path=cached_snapshot["original_path"],
                    output_path=cached_snapshot["output_path"],
                    image_url=None,
                    prompt=cached_snapshot["prompt"],
                    user_id=user_id,
                    user_copy=clean_user_copy,
                    has_logo=has_logo,
                    logo_position=stored_logo_position,
                    logo_image_hash=None,
                    logo_storage_key=None,
                )
                await crud.record_usage(
                    db,
                    request_id=generation_id,
                    model=model,
                    operation="image_edit",
                    estimated_cost=0.0,
                    cached=True,
                )
            return {
                "image_data_url": image_data_url,
                "image_url": image_url,
                "provider": "openai",
                "note": "캐시된 결과 재사용",
                "prompt": cached_snapshot["prompt"],
            }
        # 파일이 사라졌으면 캐시 미스로 떨어져 OpenAI 호출 분기로 이어진다.

    # 3) 캐시 미스: pending 행 먼저 만든 뒤 OpenAI 호출. 실패해도 흔적 남기기 위함.
    generation_id = new_generation_id()
    logger.info(
        "cache miss generation_id=%s image_hash=%s preset=%s detail=%s user_id=%s",
        generation_id,
        short_id(image_hash),
        preset.id,
        selected_detail.id,
        short_id(user_id),
    )
    await asyncio.to_thread(settings.upload_dir.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(settings.output_dir.mkdir, parents=True, exist_ok=True)
    original_path = settings.upload_dir / f"{generation_id}.{uploaded.extension}"
    output_path = settings.output_dir / f"{generation_id}.png"
    await asyncio.to_thread(original_path.write_bytes, uploaded.content)

    async with async_session_scope() as db:
        await crud.create_pending_generation(
            db,
            request_id=generation_id,
            image_hash=image_hash,
            preset_id=preset.id,
            instruction_hash=instruction_hash,
            prompt_version=prompt_version,
            model=model,
            original_path=str(original_path),
            prompt=prompt,
            user_id=user_id,
            user_copy=clean_user_copy,
            has_logo=has_logo,
            logo_position=stored_logo_position,
            logo_image_hash=None,
            logo_storage_key=None,
        )
    logger.debug(
        "generation pending generation_id=%s model=%s prompt_version=%s",
        generation_id,
        model,
        prompt_version,
    )

    try:
        openai_uploaded = await asyncio.to_thread(normalize_for_openai, uploaded)
        logger.debug(
            "OpenAI image input prepared generation_id=%s original_mime=%s "
            "original_format=%s original_mode=%s original_size=%sx%s "
            "normalized_mime=%s normalized_format=%s normalized_mode=%s "
            "normalized_size=%sx%s normalized_bytes=%s",
            generation_id,
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
        logger.debug(
            "openai call started generation_id=%s model=%s api_size=%s",
            generation_id,
            model,
            selected_detail.api_size,
        )
        b64_json = await call_openai_edit(
            uploaded=openai_uploaded,
            api_size=selected_detail.api_size,
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
        logger.exception("generation failed generation_id=%s", generation_id)
        async with async_session_scope() as db:
            await crud.mark_generation_failed(
                db,
                request_id=generation_id,
                error_message=str(exc)[:500],
            )
            await crud.record_usage(
                db,
                request_id=generation_id,
                model=model,
                operation="image_edit",
                estimated_cost=0.0,
                cached=False,
            )
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError("이미지 API 응답 이미지를 처리하지 못했습니다.") from exc

    # 4) 성공: 파일 저장 → DB success 갱신 → 사용량 기록.
    # 응답에는 /outputs/... 경로를 함께 내려준다.
    # 로컬 스토리지 단계에서는 DB에 환경별 절대 URL을 저장하지 않는다.
    image_url = output_url(output_path)
    async with async_session_scope() as db:
        await crud.mark_generation_success(
            db,
            request_id=generation_id,
            output_path=str(output_path),
            image_url=None,
        )
        await crud.record_usage(
            db,
            request_id=generation_id,
            model=model,
            operation="image_edit",
            estimated_cost=settings.openai_image_edit_estimated_cost_usd,
            cached=False,
        )
    logger.info(
        "generation success generation_id=%s image_url=%s",
        generation_id,
        image_url,
    )

    # 프론트가 별도 파일 저장 없이 바로 미리보기할 수 있도록 data URL로 반환한다.
    return {
        "image_data_url": f"data:image/png;base64,{base64.b64encode(target_png).decode('ascii')}",
        "image_url": image_url,
        "provider": "openai",
        "note": None,
        "prompt": prompt,
    }
