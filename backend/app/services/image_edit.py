"""이미지 입력 검증과 OpenAI 이미지 편집 호출."""

import asyncio
import base64
import binascii
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Literal

import httpx
from PIL import Image, ImageFilter, ImageOps

from backend.app.core.config import Settings
from backend.app.core.presets import Preset, PresetDetail
from backend.app.core.prompts import PROMPT_VERSION, build_prompt
from backend.app.db import crud
from backend.app.db.database import async_session_scope

logger = logging.getLogger(__name__)

DATA_URL_PATTERN = re.compile(
    r"^data:(image/(?:png|jpe?g|webp));base64,([A-Za-z0-9+/=]+)$",
    re.IGNORECASE,
)
ResizeMode = Literal["cover", "contain"]
SUPPORTED_UPLOAD_TYPES = ("jpg", "jpeg", "png", "webp")
SUPPORTED_UPLOAD_LABEL = "JPG, PNG, WEBP"


def _detect_image_mime(content: bytes) -> str | None:
    """파일 시그니처로 실제 이미지 MIME을 판별한다."""
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    return None


@dataclass(frozen=True)
class ImageInfo:
    """업로드 이미지의 실제 디코딩 결과. OpenAI 실패 원인 추적에 사용한다."""

    format: str
    mode: str
    width: int
    height: int


@dataclass(frozen=True)
class UploadedImage:
    """OpenAI multipart 요청에 필요한 업로드 이미지 정보."""

    mime_type: str
    content: bytes
    extension: str
    info: ImageInfo


@dataclass(frozen=True)
class TargetSize:
    """사용자가 최종으로 내려받을 이미지의 정확한 픽셀 크기."""

    width: int
    height: int


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


def _inspect_image(content: bytes) -> ImageInfo:
    """Pillow로 실제 이미지를 열어 포맷·모드·크기를 확인한다."""
    try:
        with Image.open(BytesIO(content)) as image:
            # 애니메이션/멀티프레임 이미지도 첫 프레임 기준으로 처리한다.
            image.seek(0)
            image.load()
            return ImageInfo(
                format=str(image.format or "unknown"),
                mode=image.mode,
                width=image.width,
                height=image.height,
            )
    except Exception as exc:
        raise ValueError("이미지 파일을 열 수 없습니다.") from exc


def _to_rgb_image(source: Image.Image) -> Image.Image:
    """OpenAI 입력 안정성을 위해 모든 업로드 이미지를 RGB 이미지로 맞춘다."""
    image = ImageOps.exif_transpose(source)

    # 투명 채널이 있으면 흰 배경에 합성해 광고 이미지에서 예측 가능한 RGB로 만든다.
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        background.alpha_composite(rgba)
        return background.convert("RGB")

    return image.convert("RGB")


def normalize_for_openai(uploaded: UploadedImage) -> UploadedImage:
    """OpenAI 호출 전 입력 이미지를 표준 PNG/RGB로 정규화한다.

    브라우저와 Pillow가 열 수 있는 이미지라도 CMYK, 팔레트, 일부 WebP/EXIF 조합은
    OpenAI 이미지 편집 API에서 거절될 수 있어, 외부 API에는 항상 PNG/RGB만 보낸다.
    """
    with Image.open(BytesIO(uploaded.content)) as source:
        source.seek(0)
        image = _to_rgb_image(source)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    normalized = output.getvalue()
    return UploadedImage(
        mime_type="image/png",
        content=normalized,
        extension="png",
        info=ImageInfo(
            format="PNG",
            mode="RGB",
            width=image.width,
            height=image.height,
        ),
    )


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


def parse_image(data_url: str, max_upload_bytes: int) -> UploadedImage:
    """프론트가 보낸 data URL을 검증하고 이미지 바이트로 변환한다."""
    match = DATA_URL_PATTERN.match(data_url or "")
    if not match:
        raise ValueError(f"{SUPPORTED_UPLOAD_LABEL} 이미지만 업로드할 수 있습니다.")

    mime_type = match.group(1).lower().replace("image/jpg", "image/jpeg")
    try:
        # validate=True로 깨진 base64가 500이 아니라 사용자 입력 오류가 되게 한다.
        content = base64.b64decode(match.group(2), validate=True)
    except binascii.Error as exc:
        raise ValueError("이미지 데이터가 올바른 base64 형식이 아닙니다.") from exc

    if not content or len(content) > max_upload_bytes:
        raise ValueError("이미지는 50MB 이하만 업로드할 수 있습니다.")

    detected_mime = _detect_image_mime(content)
    if detected_mime is None:
        raise ValueError("이미지 파일 형식을 확인할 수 없습니다.")
    if detected_mime != mime_type:
        raise ValueError("이미지 MIME 타입과 실제 파일 형식이 일치하지 않습니다.")

    info = _inspect_image(content)
    extension = "jpg" if mime_type == "image/jpeg" else mime_type.split("/")[-1]
    return UploadedImage(
        mime_type=mime_type,
        content=content,
        extension=extension,
        info=info,
    )


def _render_cover(image: Image.Image, target_size: TargetSize) -> Image.Image:
    """캔버스를 꽉 채우고 남는 영역은 중앙 기준으로 잘라낸다."""
    return ImageOps.fit(
        image,
        (target_size.width, target_size.height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def _render_contain(image: Image.Image, target_size: TargetSize) -> Image.Image:
    """원본 전체가 보이도록 맞추고, 남는 영역은 흐림 배경으로 채운다."""
    canvas_size = (target_size.width, target_size.height)
    background = _render_cover(image, target_size)
    blur_radius = max(target_size.width, target_size.height) // 28
    background = background.filter(ImageFilter.GaussianBlur(max(8, blur_radius)))

    foreground = image.copy()
    foreground.thumbnail(canvas_size, Image.Resampling.LANCZOS)
    x = (target_size.width - foreground.width) // 2
    y = (target_size.height - foreground.height) // 2
    background.paste(foreground, (x, y))
    return background


def render_target_png(
    content: bytes,
    target_size: TargetSize,
    resize_mode: ResizeMode = "cover",
) -> bytes:
    """이미지 바이트를 선택한 상세 사이즈의 PNG로 정확히 맞춘다.

    OpenAI가 지원하는 생성 크기와 실제 광고 게시 규격은 다를 수 있으므로,
    모델 결과를 받은 뒤 선택한 리사이즈 정책으로 최종 픽셀 크기를 고정한다.
    """
    with Image.open(BytesIO(content)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        if resize_mode == "contain":
            fitted = _render_contain(image, target_size)
        else:
            fitted = _render_cover(image, target_size)

    output = BytesIO()
    fitted.save(output, format="PNG", optimize=True)
    return output.getvalue()


async def _file_to_data_url(path: Path) -> str:
    """저장된 PNG 파일을 base64 data URL로 인코딩한다(캐시 hit 응답용)."""
    content = await asyncio.to_thread(path.read_bytes)
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _extract_b64_json(payload: object) -> str:
    """OpenAI 이미지 응답에서 결과 base64를 안전하게 꺼낸다."""
    if not isinstance(payload, dict):
        raise RuntimeError("이미지 API 응답 형식이 올바르지 않습니다.")

    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise RuntimeError("이미지 API 응답에 결과 이미지가 없습니다.")

    first_item = data[0]
    if not isinstance(first_item, dict):
        raise RuntimeError("이미지 API 응답 형식이 올바르지 않습니다.")

    b64_json = first_item.get("b64_json")
    if not isinstance(b64_json, str) or not b64_json.strip():
        raise RuntimeError("이미지 API 응답에 결과 이미지가 없습니다.")

    return b64_json


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
    try:
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
    except httpx.HTTPError as exc:
        # 네트워크 실패·타임아웃·DNS 등은 사용자 잘못이 아니라 외부 의존성 문제 → RuntimeError.
        raise RuntimeError("이미지 API에 연결하지 못했습니다.") from exc

    try:
        # 오류 응답도 JSON으로 오는 경우가 많아 먼저 payload로 통일한다.
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("이미지 API 응답을 해석하지 못했습니다.") from exc

    if response.status_code >= 400:
        message = "이미지 생성에 실패했습니다."
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                message = str(error.get("message") or message)
        logger.warning(
            "OpenAI image edit failed status=%s model=%s message=%s",
            response.status_code,
            settings.openai_image_model,
            message,
        )
        raise RuntimeError(message)

    return _extract_b64_json(payload)


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
    """설정된 provider에 따라 mock 반환 또는 OpenAI 이미지 편집을 수행한다.

    openai 모드에서는 동일 입력(이미지+프리셋+feedback+모델+프롬프트 버전)이면
    DB 캐시를 재사용하고, 실패해도 DB에 흔적을 남긴다. mock 모드는 DB·캐시 모두
    건너뛰어 로컬 플로우만 검증한다.
    """
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

    # 2) 캐시 미스: pending 행 먼저 만든 뒤 OpenAI 호출. 실패해도 흔적 남기기 위함.
    request_id = _new_request_id()
    await asyncio.to_thread(settings.upload_dir.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread(settings.output_dir.mkdir, parents=True, exist_ok=True)
    # 원본은 uploads/, 결과는 outputs/에 같은 request_id로 짝지어 저장한다.
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
        b64_json = await _call_openai_edit(
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
        "image_data_url": f"data:image/png;base64,{base64.b64encode(target_png).decode('ascii')}",
        "provider": "openai",
        "note": None,
        "prompt": prompt,
    }
