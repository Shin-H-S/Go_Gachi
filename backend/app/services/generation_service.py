"""광고 이미지 생성 전체 흐름 조립."""

import asyncio
import base64
import logging

from backend.app.core.config import Settings
from backend.app.core.errors import ServiceError
from backend.app.core.logging_utils import short_id
from backend.app.core.presets import Preset, PresetDetail
from backend.app.core.prompts import PROMPT_VERSION, build_prompt
from backend.app.db import crud
from backend.app.db.database import async_session_scope
from backend.app.services.copywriting import AdCopy
from backend.app.services.costs import calculate_image_cost
from backend.app.services.generation_cache import cached_response, find_cache_snapshot
from backend.app.services.generation_copy import cache_instruction, rendered_copy_text
from backend.app.services.generation_files import new_generation_id
from backend.app.services.generation_inputs import target_size_or_detail, user_prompt_with_context
from backend.app.services.generation_storage import prepare_storage, save_output
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
    text_copy: AdCopy | None = None,
) -> dict[str, str | None]:
    """설정된 provider에 따라 mock 반환 또는 OpenAI 이미지 편집을 수행한다.

    user_id가 있으면 생성 기록에 소유자로 남긴다(비로그인이면 None,
    캐시 조회 키에는 영향을 주지 않는다).
    """
    # provider와 무관하게 먼저 입력 이미지를 검증해 프론트 오류를 빠르게 돌려준다.
    uploaded = parse_image(image_data_url, settings.max_upload_bytes)
    logo_uploaded = (
        parse_image(logo_data_url, settings.max_upload_bytes)
        if logo_data_url and logo_data_url.strip()
        else None
    )
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
    text_model: str | None = settings.openai_text_model if text_copy is not None else None
    logo_image_hash: str | None = (
        crud.image_sha256(logo_uploaded.content) if logo_uploaded else None
    )
    has_logo: bool = logo_uploaded is not None
    stored_logo_position: str | None = logo_position if has_logo else None
    cache_input = cache_instruction(
        generation_user_prompt,
        text_copy,
        user_copy=clean_user_copy,
        has_logo=has_logo,
        logo_position=stored_logo_position,
        logo_image_hash=logo_image_hash,
    )

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
        raise ServiceError("OPENAI_API_KEY_MISSING", "OPENAI_API_KEY가 설정되지 않았습니다.")

    prompt = build_prompt(
        preset,
        generation_user_prompt,
        selected_detail,
        image_copy=text_copy,
        logo_position=stored_logo_position,
    )
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
        text_model=text_model,
        has_logo=has_logo,
        logo_position=stored_logo_position,
        logo_image_hash=logo_image_hash,
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
    try:
        paths = await prepare_storage(
            generation_id=generation_id,
            image_hash=image_hash,
            uploaded=uploaded,
            settings=settings,
        )
    except Exception as exc:
        logger.exception("generation storage prepare failed generation_id=%s", generation_id)
        raise ServiceError(
            "IMAGE_STORAGE_PREPARE_FAILED",
            "이미지 저장소를 준비하지 못했습니다.",
        ) from exc

    async with async_session_scope() as db:
        await crud.create_pending_generation(
            db,
            request_id=generation_id,
            image_hash=image_hash,
            preset_id=preset.id,
            instruction_hash=instruction_hash,
            prompt_version=prompt_version,
            model=model,
            original_path=paths.original_path,
            prompt=prompt,
            text_model=text_model,
            user_id=user_id,
            user_copy=stored_user_copy,
            has_logo=has_logo,
            logo_position=stored_logo_position,
            logo_image_hash=logo_image_hash,
            logo_storage_key=None,
        )
    logger.debug(
        "generation pending generation_id=%s model=%s prompt_version=%s",
        generation_id,
        model,
        prompt_version,
    )

    try:
        try:
            openai_uploaded = await asyncio.to_thread(normalize_for_openai, uploaded)
            openai_logo_uploaded = (
                await asyncio.to_thread(normalize_for_openai, logo_uploaded)
                if logo_uploaded
                else None
            )
        except Exception as exc:
            raise ServiceError(
                "IMAGE_INPUT_NORMALIZE_FAILED",
                "OpenAI 호출 전 입력 이미지를 정규화하지 못했습니다.",
            ) from exc
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
        if openai_logo_uploaded:
            logger.debug(
                "OpenAI logo reference prepared generation_id=%s original_mime=%s "
                "original_format=%s original_mode=%s original_size=%sx%s "
                "normalized_mime=%s normalized_format=%s normalized_mode=%s "
                "normalized_size=%sx%s normalized_bytes=%s logo_hash=%s",
                generation_id,
                logo_uploaded.mime_type,
                logo_uploaded.info.format,
                logo_uploaded.info.mode,
                logo_uploaded.info.width,
                logo_uploaded.info.height,
                openai_logo_uploaded.mime_type,
                openai_logo_uploaded.info.format,
                openai_logo_uploaded.info.mode,
                openai_logo_uploaded.info.width,
                openai_logo_uploaded.info.height,
                len(openai_logo_uploaded.content),
                short_id(logo_image_hash),
            )
        logger.debug(
            "openai call started generation_id=%s model=%s api_size=%s reference_images=%s",
            generation_id,
            model,
            selected_detail.api_size,
            1 if openai_logo_uploaded else 0,
        )
        try:
            b64_json, image_usage = await call_openai_edit(
                uploaded=openai_uploaded,
                reference_images=[openai_logo_uploaded] if openai_logo_uploaded else None,
                api_size=selected_detail.api_size,
                prompt=prompt,
                settings=settings,
            )
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(
                "IMAGE_API_CALL_FAILED",
                "이미지 API 호출 중 문제가 발생했습니다.",
            ) from exc

        try:
            # OpenAI가 응답은 했지만 결과 이미지 base64가 깨졌다면 별도 응답 오류로 본다.
            decoded = base64.b64decode(b64_json, validate=True)
        except Exception as exc:
            raise ServiceError(
                "IMAGE_RESULT_DECODE_FAILED",
                "이미지 API 결과를 디코딩하지 못했습니다.",
            ) from exc

        try:
            target_png = await asyncio.to_thread(
                render_target_png,
                decoded,
                target_size,
                resize_mode,
            )
        except Exception as exc:
            raise ServiceError(
                "IMAGE_RESULT_PROCESS_FAILED",
                "이미지 API 결과를 처리하지 못했습니다.",
            ) from exc

        try:
            await save_output(output_path=paths.output_path, body=target_png, settings=settings)
        except Exception as exc:
            raise ServiceError(
                "IMAGE_STORAGE_SAVE_FAILED",
                "결과 이미지를 저장하지 못했습니다.",
            ) from exc
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
                cost_usd=0.0,
                cached=False,
            )
        if isinstance(exc, ServiceError):
            raise
        raise ServiceError(
            "IMAGE_GENERATION_FAILED",
            "이미지 생성 처리 중 문제가 발생했습니다.",
        ) from exc

    # 4) 성공: 파일 저장 → DB success 갱신 → 사용량 기록.
    # 응답에는 외부 접근 URL(local: /outputs/..., r2: public URL)을 함께 내려준다.
    # DB에는 환경별 절대 URL을 박지 않고 path/key만 저장한다.
    image_url = output_url(paths.output_path)
    # usage가 비어 있으면(테스트·옛 모델) quality 기반 보수적 추정 단가로 폴백한다.
    actual_cost = calculate_image_cost(image_usage, quality=settings.openai_image_quality)
    async with async_session_scope() as db:
        await crud.mark_generation_success(
            db,
            request_id=generation_id,
            output_path=paths.output_path,
            image_url=None,
        )
        await crud.record_usage(
            db,
            request_id=generation_id,
            model=model,
            operation="image_edit",
            cost_usd=actual_cost,
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
