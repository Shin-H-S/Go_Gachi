"""광고 이미지 생성 전체 흐름 조립."""

import asyncio
import base64
import logging

from backend.app.core.config import Settings
from backend.app.core.logging_utils import short_id
from backend.app.core.presets import Preset, PresetDetail
from backend.app.core.prompts import PROMPT_VERSION, build_prompt
from backend.app.core.text_layouts import find_text_layout
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.services.copywriting import AdCopy
from backend.app.services.generation_cache import cached_response, find_cache_snapshot
from backend.app.services.generation_copy import cache_instruction, rendered_copy_text
from backend.app.services.generation_files import new_generation_id
from backend.app.services.generation_inputs import target_size_or_detail, user_prompt_with_context
from backend.app.services.image_processing import normalize_for_openai, render_target_png
from backend.app.services.image_types import ResizeMode
from backend.app.services.image_validation import parse_image
from backend.app.services.openai_images import call_openai_edit
from backend.app.services.storage import get_storage
from backend.app.services.storage_url import output_url
from backend.app.services.text_overlay import render_text_overlay

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
    text_copy: AdCopy | None = None,
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
    generation_user_prompt: str = user_prompt_with_context(
        user_prompt,
        target_size,
        selected_detail,
        resize_mode,
    )
    clean_user_copy: str | None = (user_copy or "").strip() or None
    stored_user_copy: str | None = rendered_copy_text(text_copy)
    has_logo: bool = bool(logo_data_url and logo_data_url.strip())
    stored_logo_position: str | None = logo_position if has_logo else None
    cache_input = cache_instruction(
        generation_user_prompt,
        text_copy,
        user_copy=clean_user_copy,
        has_logo=has_logo,
        logo_position=stored_logo_position,
    )

    if settings.image_provider == "mock":
        # mock은 GCP 배포/프론트 연동 흐름만 확인할 때 사용한다.
        target_png = render_target_png(uploaded.content, target_size, resize_mode)
        if text_copy:
            layout = find_text_layout(preset.id, selected_detail.id)
            target_png = render_text_overlay(target_png, text_copy, layout, settings)
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
    instruction_hash = crud.instruction_sha256(cache_input)
    model = settings.openai_image_model
    prompt_version = PROMPT_VERSION

    cache_snapshot = await find_cache_snapshot(
        settings=settings,
        image_hash=image_hash,
        preset_id=preset.id,
        instruction_hash=instruction_hash,
        model=model,
        prompt_version=prompt_version,
    )
    cache_result = await cached_response(
        cache_snapshot,
        settings=settings,
        user_id=user_id,
        user_copy=stored_user_copy,
        has_logo=has_logo,
        logo_position=stored_logo_position,
    )
    if cache_result is not None:
        return cache_result
    # 캐시 행이 없거나 파일이 사라졌으면 캐시 미스로 떨어져 OpenAI 호출 분기로 이어진다.

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
    storage = get_storage(settings)
    output_storage_path = storage.output_path(generation_id)
    if settings.storage_backend == "r2":
        original_storage_path = storage.original_path(
            image_hash=image_hash,
            extension=uploaded.extension,
            generation_id=generation_id,
        )
        if not await storage.exists(original_storage_path):
            await storage.write_bytes(
                original_storage_path,
                body=uploaded.content,
                content_type=uploaded.mime_type,
            )
    else:
        # local 모드: 디스크에 저장. 같은 image_hash의 원본이 이미 있으면 그 경로를 재사용한다.
        async with async_session_scope() as db:
            old_path = await crud.find_original_path(db, image_hash=image_hash)
        if old_path:
            original_storage_path = old_path
        else:
            original_storage_path = storage.original_path(
                image_hash=image_hash,
                extension=uploaded.extension,
                generation_id=generation_id,
            )
            await storage.write_bytes(
                original_storage_path,
                body=uploaded.content,
                content_type=uploaded.mime_type,
            )

    async with async_session_scope() as db:
        await crud.create_pending_generation(
            db,
            request_id=generation_id,
            image_hash=image_hash,
            preset_id=preset.id,
            instruction_hash=instruction_hash,
            prompt_version=prompt_version,
            model=model,
            original_path=original_storage_path,
            prompt=prompt,
            user_id=user_id,
            user_copy=stored_user_copy,
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
        if text_copy:
            layout = find_text_layout(preset.id, selected_detail.id)
            target_png = await asyncio.to_thread(
                render_text_overlay,
                target_png,
                text_copy,
                layout,
                settings,
            )
        await storage.write_bytes(
            output_storage_path,
            body=target_png,
            content_type="image/png",
        )
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
    # 응답에는 외부 접근 URL(local: /outputs/..., r2: public URL)을 함께 내려준다.
    # DB에는 환경별 절대 URL을 박지 않고 path/key만 저장한다.
    image_url = output_url(output_storage_path)
    async with async_session_scope() as db:
        await crud.mark_generation_success(
            db,
            request_id=generation_id,
            output_path=output_storage_path,
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
