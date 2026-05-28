"""Generation/ApiUsage 테이블 읽기·쓰기 함수.

상태 전이: create_pending → mark_*_success / mark_*_failed.
캐시 hit 시엔 create_cached_generation으로 별도 행을 남겨 감사 로그를 유지한다.
"""

import hashlib
import re
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import ApiUsage, Generation

_WHITESPACE_RE = re.compile(r"\s+")


def image_sha256(file_bytes: bytes) -> str:
    """업로드 이미지 바이트의 SHA256 해시(64자) — 캐시 키의 핵심 요소.

    Args:
        file_bytes: 해싱할 원본 바이트.
    Returns:
        64자 16진수 문자열.
    """
    return hashlib.sha256(file_bytes).hexdigest()


def normalize_instruction(feedback: str | None) -> str:
    """사용자 추가 지시문(feedback)을 캐시 키용으로 정규화한다.

    None·빈 문자열·공백만 있는 입력은 모두 ``""``로 통일하고,
    그 외에는 앞뒤 공백을 잘라낸 뒤 내부 연속 공백·줄바꿈을 한 칸으로 압축한다.

    Args:
        feedback: 원본 지시문(None 가능).
    Returns:
        정규화된 문자열(빈 문자열일 수 있음).
    """
    if not feedback:
        return ""
    stripped = feedback.strip()
    if not stripped:
        return ""
    return _WHITESPACE_RE.sub(" ", stripped)


def instruction_sha256(feedback: str | None) -> str:
    """정규화된 지시문의 SHA256 해시.

    빈 지시문도 결정적인 단일 해시 값으로 매핑되어, 캐시 키 계산이 항상 안정적이다.

    Args:
        feedback: 원본 지시문(None 가능).
    Returns:
        64자 16진수 문자열.
    """
    normalized = normalize_instruction(feedback)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def find_cached_generation(
    db: AsyncSession,
    *,
    image_hash: str,
    preset_id: str,
    instruction_hash: str,
    model: str,
    prompt_version: str,
) -> Generation | None:
    """재사용 가능한 성공 생성 기록을 찾는다.

    가장 최근 success 행부터 훑되, 결과 파일이 실제로 디스크에 남아있는 것만 선택.
    파일이 삭제된 옛 기록은 자동으로 건너뛰고 그 다음 후보로 fallback 한다.

    Args:
        db: 활성 DB 세션.
        image_hash: 업로드 이미지의 SHA256.
        preset_id: 프리셋 ID(예: instagram_feed_square).
        instruction_hash: 정규화된 feedback의 SHA256.
        model: 사용한 OpenAI 모델 ID.
        prompt_version: 프롬프트 판본 라벨.
    Returns:
        조건을 만족하는 가장 최신 Generation, 없으면 None.
    """
    stmt = (
        select(Generation)
        .where(Generation.image_hash == image_hash)
        .where(Generation.preset_id == preset_id)
        .where(Generation.instruction_hash == instruction_hash)
        .where(Generation.model == model)
        .where(Generation.prompt_version == prompt_version)
        .where(Generation.status == "success")
        .order_by(Generation.created_at.desc(), Generation.id.desc())
    )
    # 최신부터 순회하며 파일이 실제로 존재하는 첫 행을 반환. 없으면 None.
    result = await db.execute(stmt)
    for generation in result.scalars():
        if generation.output_path and Path(generation.output_path).exists():
            return generation
    return None


async def create_pending_generation(
    db: AsyncSession,
    *,
    request_id: str,
    image_hash: str,
    preset_id: str,
    instruction_hash: str,
    prompt_version: str,
    model: str,
    original_path: str | None,
    prompt: str | None,
) -> Generation:
    """OpenAI 호출 직전, 'pending' 상태로 행을 먼저 만든다.

    OpenAI가 도중에 실패해도 시도 자체의 흔적이 남아 디버깅/통계에 쓰인다.
    뒤이어 mark_generation_success 또는 mark_generation_failed가 같은 행을 갱신.

    Args:
        db: 활성 DB 세션.
        request_id: 요청 식별 UUID(라우터에서 발급).
        image_hash: 업로드 이미지의 SHA256.
        preset_id: 프리셋 ID.
        instruction_hash: 정규화된 feedback의 SHA256.
        prompt_version: 프롬프트 판본 라벨.
        model: 사용할 OpenAI 모델 ID.
        original_path: 원본 사진 저장 경로(있으면 문자열).
        prompt: OpenAI에 보낼 프롬프트 본문.
    Returns:
        새로 만들어진 pending Generation 행.
    """
    generation = Generation(
        request_id=request_id,
        image_hash=image_hash,
        preset_id=preset_id,
        instruction_hash=instruction_hash,
        prompt_version=prompt_version,
        model=model,
        original_path=original_path,
        output_path=None,
        image_url=None,
        prompt=prompt,
        status="pending",
        error_message=None,
    )
    db.add(generation)
    await db.flush()
    return generation


async def mark_generation_success(
    db: AsyncSession,
    *,
    request_id: str,
    output_path: str,
    image_url: str | None,
) -> Generation:
    """pending 행을 success로 갱신하고 결과 경로/URL을 채워 넣는다.

    Args:
        db: 활성 DB 세션.
        request_id: 갱신할 행을 찾을 키(create_pending_generation에서 발급된 것).
        output_path: 결과 png 파일의 디스크 경로.
        image_url: 프론트에 돌려줄 정적 URL(없으면 None).
    Returns:
        갱신된 Generation 행.
    """
    result = await db.execute(select(Generation).where(Generation.request_id == request_id))
    generation = result.scalar_one()
    generation.output_path = output_path
    generation.image_url = image_url
    generation.status = "success"
    # 이전에 잘못 적혔을 수 있는 에러 메시지는 명시적으로 비운다.
    generation.error_message = None
    await db.flush()
    return generation


async def mark_generation_failed(
    db: AsyncSession,
    *,
    request_id: str,
    error_message: str,
) -> Generation:
    """pending 행을 failed로 갱신하고 사유 메시지를 기록한다.

    Args:
        db: 활성 DB 세션.
        request_id: 갱신할 행을 찾을 키.
        error_message: 실패 사유(예외 메시지 등).
    Returns:
        갱신된 Generation 행.
    """
    result = await db.execute(select(Generation).where(Generation.request_id == request_id))
    generation = result.scalar_one()
    generation.status = "failed"
    generation.error_message = error_message
    await db.flush()
    return generation


async def create_cached_generation(
    db: AsyncSession,
    *,
    request_id: str,
    image_hash: str,
    preset_id: str,
    instruction_hash: str,
    prompt_version: str,
    model: str,
    original_path: str | None,
    output_path: str | None,
    image_url: str | None,
    prompt: str | None,
) -> Generation:
    """캐시 hit 요청도 별도 'cached' 행으로 남겨 감사·통계 로그를 유지한다.

    원본 success 행의 필드를 호출 측에서 미리 스냅샷해 넘긴다. 세션 경계를 넘은
    detached ORM 인스턴스에 의존하지 않도록 명시 인자만 받는다(파일은 원본 행의
    output_path를 그대로 재사용).

    Args:
        db: 활성 DB 세션.
        request_id: 이번 캐시 hit 요청의 식별 UUID.
        image_hash: 원본 행에서 복사할 이미지 해시.
        preset_id: 원본 행의 프리셋 ID.
        instruction_hash: 원본 행의 지시문 해시.
        prompt_version: 원본 행의 프롬프트 버전.
        model: 원본 행의 모델 ID.
        original_path: 원본 사진 경로(없을 수 있음).
        output_path: 원본 결과 파일 경로.
        image_url: 원본 결과 URL(없을 수 있음).
        prompt: 원본 행의 프롬프트 본문.
    Returns:
        새로 만들어진 cached Generation 행.
    """
    generation = Generation(
        request_id=request_id,
        image_hash=image_hash,
        preset_id=preset_id,
        instruction_hash=instruction_hash,
        prompt_version=prompt_version,
        model=model,
        original_path=original_path,
        output_path=output_path,
        image_url=image_url,
        prompt=prompt,
        status="cached",
        error_message=None,
    )
    db.add(generation)
    await db.flush()
    return generation


async def record_usage(
    db: AsyncSession,
    *,
    request_id: str,
    model: str,
    operation: str,
    estimated_cost: float,
    cached: bool,
) -> ApiUsage:
    """OpenAI 호출 1건의 추정 비용/캐시 여부를 기록한다.

    캐시 hit이면 estimated_cost=0.0, cached=True. 실제 호출이면 양수, cached=False.

    Args:
        db: 활성 DB 세션.
        request_id: 요청 식별 UUID(Generation 행과 짝).
        model: 사용한 OpenAI 모델 ID.
        operation: 호출 작업 종류(예: "image_edit").
        estimated_cost: 이번 호출의 추정 USD 비용.
        cached: 실제 호출 없이 캐시로 처리됐는지 여부.
    Returns:
        새로 만들어진 ApiUsage 행.
    """
    usage = ApiUsage(
        request_id=request_id,
        provider="openai",
        model=model,
        operation=operation,
        estimated_cost=estimated_cost,
        cached=cached,
    )
    db.add(usage)
    await db.flush()
    return usage


async def usage_summary(db: AsyncSession) -> dict[str, float | int]:
    """누적 비용·요청 수·캐시 hit 수를 한 번에 집계한다(/internal/usage 응답용).

    Args:
        db: 활성 DB 세션.
    Returns:
        ``{"total_estimated_cost": float, "generation_count": int, "cached_count": int}``.
    """
    # 비용 합계: 빈 테이블이면 sum이 None이라 coalesce로 0.0 보정.
    total_result = await db.execute(select(func.coalesce(func.sum(ApiUsage.estimated_cost), 0.0)))
    total_cost = total_result.scalar_one()
    generation_result = await db.execute(select(func.count()).select_from(Generation))
    generation_count = generation_result.scalar_one()
    # cached_count는 ApiUsage 기준(같은 request_id의 Generation 'cached' 상태와 짝).
    cached_result = await db.execute(
        select(func.count()).select_from(ApiUsage).where(ApiUsage.cached.is_(True))
    )
    cached_count = cached_result.scalar_one()
    return {
        "total_estimated_cost": float(total_cost),
        "generation_count": int(generation_count),
        "cached_count": int(cached_count),
    }
