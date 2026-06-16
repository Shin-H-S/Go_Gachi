"""OpenAI Responses API로 광고 문구를 생성한다."""

import json
import logging
import time
from dataclasses import dataclass, field

import httpx
from pydantic import ValidationError

from backend.app.core.config import Settings
from backend.app.core.errors import ServiceError
from backend.app.core.presets import Preset, PresetDetail
from backend.app.schemas import CopyMode
from backend.app.services.copywriting import AdCopy, build_ad_copy

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CopyGenerationResult:
    copy: AdCopy
    usage: dict[str, object] = field(default_factory=dict)
    used_openai: bool = False


COPY_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "headline": {"type": ["string", "null"]},
        "subcopy": {"type": ["string", "null"]},
        "cta": {"type": ["string", "null"]},
    },
    "required": ["headline", "subcopy", "cta"],
}


def _extract_output_text(payload: object) -> str:
    """Responses API 응답에서 텍스트 출력을 꺼낸다."""
    if not isinstance(payload, dict):
        raise ServiceError(
            "COPY_API_RESPONSE_INVALID",
            "문구 생성 API 응답 형식이 올바르지 않습니다.",
        )

    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output = payload.get("output")
    if not isinstance(output, list):
        raise ServiceError("COPY_API_RESULT_EMPTY", "문구 생성 API 응답에 출력이 없습니다.")

    texts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                texts.append(text)

    if not texts:
        raise ServiceError("COPY_API_RESULT_EMPTY", "문구 생성 API 응답에 출력 텍스트가 없습니다.")
    return "\n".join(texts)


def _extract_usage(payload: object) -> dict[str, object]:
    """Responses API 응답에서 token usage를 꺼낸다."""
    if not isinstance(payload, dict):
        return {}
    usage = payload.get("usage")
    return usage if isinstance(usage, dict) else {}


def _parse_copy_json(text: str, copy_mode: CopyMode) -> AdCopy:
    """모델이 반환한 JSON을 AdCopy로 검증한다."""
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ServiceError(
            "COPY_API_JSON_PARSE_FAILED",
            "문구 생성 API 응답 JSON을 해석하지 못했습니다.",
        ) from exc

    if not isinstance(raw, dict):
        raise ServiceError(
            "COPY_API_JSON_INVALID",
            "문구 생성 API 응답 JSON 형식이 올바르지 않습니다.",
        )

    try:
        return AdCopy(
            headline=raw.get("headline"),
            subcopy=raw.get("subcopy"),
            cta=raw.get("cta"),
            mode=copy_mode,
        )
    except ValidationError as exc:
        raise ServiceError(
            "COPY_API_VALIDATION_FAILED",
            "문구 생성 API 응답 검증에 실패했습니다.",
        ) from exc


def _copy_system_prompt(copy_mode: CopyMode) -> str:
    """광고 문구 모델에 전달할 고정 지시문."""
    return (
        "You are a Korean advertising copywriter for a small local cafe. "
        "Write copy as if it will be placed on a cafe drink poster. "
        "Return only valid JSON with three fields: headline, subcopy, and cta. "
        "Use only Korean in all output. "
        "Do not transliterate Korean into English or mix Korean and English "
        "unless the user explicitly provided them. "
        "Do not output any text beyond the required JSON. "
        "Headlines should be short, punchy, and designed for visual emphasis. "
        "For the headline field, generate a Korean advertising headline suitable "
        "for image banners. "
        "Input text may describe product characteristics, taste, mood, or benefits. "
        "Rewrite the input into a short promotional headline instead of restating it. "
        "Preserve the original meaning but compress into a marketing headline. "
        "Target 6-18 Korean characters for headline text. "
        "Prefer noun phrases or short emotional phrases. "
        "Sound natural for café, food, and commercial banners. "
        "Remove explanatory wording and unnecessary particles. "
        "Highlight sensory experience, atmosphere, or key product value. "
        "Allow expressive reinterpretation instead of literal conversion. "
        "Avoid full sentence descriptions. "
        "Avoid CTA phrases, commands, quotation marks, emojis, hashtags, or "
        "punctuation in headline. "
        "Subcopy should be a complete natural supporting sentence that reinforces the headline. "
        "CTA should be direct, imperative, and easy to act on. "
        "Create copy that can be rendered directly inside an image overlay. "
        "Avoid awkward truncation, partial phrases, or unnatural word breaks. "
        "Preserve exact menu names, prices, dates, quantities, and discount numbers "
        "from the user copy. "
        "Do not invent awards, addresses, phone numbers, brand names, or unavailable claims. "
        "Do not add any extra text beyond the required headline, subcopy, and cta fields. "
        "Keep subcopy brief enough to fit cleanly on the image, while remaining a full sentence. "
        "Keep CTA short and action-oriented. "
        "If copyMode is preserve, keep the user's copy as close as possible and only "
        "normalize spacing and price format. "
        "If copyMode is polish, turn the user's copy into polished ad copy with a strong "
        "headline, one natural supporting line, and an optional CTA. "
        "If copyMode is rewrite, rewrite the user's copy into fully promotional ad copy with "
        "a confident headline, supportive subcopy, and a clear call to action. "
        "For rewrite, prefer short, slogan-style phrases that preserve the user's "
        "original product theme, taste, mood, and benefit. "
        "Use the examples only as style references, not as fixed content: '깊은 우유 풍미의 라떼', "
        "'우유가 살아있는 라떼', '진한 우유의 깊은 맛', or '우유의 깊이를 담다'. "
        "Do not reuse example themes, ingredients, flavors, or product concepts directly. "
        "Base copy on the actual product. Avoid unsupported ingredients, flavors, "
        "and coffee-specific messaging for non-coffee drinks. "
        "Keep the output concise, natural, and commercial without forcing any "
        "specific ingredient, flavor, or product theme. "        
        f"copyMode: {copy_mode}"
    )


def _copy_user_prompt(
    *,
    preset: Preset,
    detail: PresetDetail | None,
    user_prompt: str,
    user_copy: str,
) -> str:
    """문구 생성에 필요한 채널/상세/사용자 맥락을 묶는다."""
    return "\n".join(
        [
            f"Channel: {preset.label} ({preset.id})",
            f"Detail: {detail.label} ({detail.id})" if detail else "Detail: default",
            f"Image direction request: {(user_prompt or '').strip() or 'none'}",
            f"User copy to improve: {(user_copy or '').strip() or 'none'}",
        ]
    )


async def call_openai_copy(
    *,
    settings: Settings,
    preset: Preset,
    detail: PresetDetail | None,
    user_prompt: str,
    user_copy: str,
    copy_mode: CopyMode,
) -> CopyGenerationResult:
    """Responses API로 광고 문구를 생성하고 AdCopy로 반환한다."""
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openai_text_model,
                    "input": [
                        {"role": "system", "content": _copy_system_prompt(copy_mode)},
                        {
                            "role": "user",
                            "content": _copy_user_prompt(
                                preset=preset,
                                detail=detail,
                                user_prompt=user_prompt,
                                user_copy=user_copy,
                            ),
                        },
                    ],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "ad_copy",
                            "schema": COPY_JSON_SCHEMA,
                            "strict": True,
                        }
                    },
                },
            )
    except httpx.TimeoutException as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.warning(
            "OpenAI copy generation timed out model=%s took=%.1fms error=%s",
            settings.openai_text_model,
            elapsed_ms,
            type(exc).__name__,
        )
        raise ServiceError("COPY_API_TIMEOUT", "문구 생성 API 응답 시간이 초과되었습니다.") from exc
    except httpx.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.warning(
            "OpenAI copy generation connection failed model=%s took=%.1fms error=%s",
            settings.openai_text_model,
            elapsed_ms,
            type(exc).__name__,
        )
        raise ServiceError(
            "COPY_API_CONNECTION_FAILED",
            "문구 생성 API에 연결하지 못했습니다.",
        ) from exc

    elapsed_ms = (time.perf_counter() - start) * 1000
    openai_request_id = response.headers.get("x-request-id")
    try:
        payload = response.json()
    except ValueError as exc:
        raise ServiceError(
            "COPY_API_RESPONSE_PARSE_FAILED",
            "문구 생성 API 응답을 해석하지 못했습니다.",
        ) from exc

    if response.status_code >= 400:
        raw_message = "문구 생성에 실패했습니다."
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                raw_message = str(error.get("message") or raw_message)
        logger.warning(
            "OpenAI copy generation failed status=%s model=%s took=%.1fms "
            "openai_request_id=%s message=%s",
            response.status_code,
            settings.openai_text_model,
            elapsed_ms,
            openai_request_id or "-",
            raw_message,
        )
        raise ServiceError("COPY_API_REJECTED", "문구 생성 요청이 외부 API에서 거절되었습니다.")

    usage = _extract_usage(payload)
    logger.info(
        "OpenAI copy generation finished status=%s model=%s took=%.1fms "
        "openai_request_id=%s input_tokens=%s output_tokens=%s",
        response.status_code,
        settings.openai_text_model,
        elapsed_ms,
        openai_request_id or "-",
        usage.get("input_tokens", "-"),
        usage.get("output_tokens", "-"),
    )
    return CopyGenerationResult(
        copy=_parse_copy_json(_extract_output_text(payload), copy_mode),
        usage=usage,
        used_openai=True,
    )


async def generate_ad_copy(
    *,
    settings: Settings,
    preset: Preset,
    detail: PresetDetail | None,
    user_prompt: str,
    user_copy: str,
    copy_mode: CopyMode,
) -> CopyGenerationResult:
    """실행 환경에 맞게 AI 문구 생성 또는 로컬 fallback을 수행한다."""
    if settings.image_provider != "openai" or not settings.openai_api_key:
        # mock/로컬 키 없음 상태에서는 userPrompt를 문구로 오해하지 않도록 userCopy만 사용한다.
        return CopyGenerationResult(copy=build_ad_copy(user_copy, copy_mode))

    if copy_mode == "preserve" and user_copy.strip():
        # 그대로 사용은 모델 호출보다 사용자 입력 보존이 더 중요하다.
        return CopyGenerationResult(copy=build_ad_copy(user_copy, copy_mode))

    return await call_openai_copy(
        settings=settings,
        preset=preset,
        detail=detail,
        user_prompt=user_prompt,
        user_copy=user_copy,
        copy_mode=copy_mode,
    )
