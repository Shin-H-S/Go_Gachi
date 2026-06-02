"""Generation/ApiUsage 테이블 읽기·쓰기 함수.

상태 전이: create_pending → mark_*_success / mark_*_failed.
캐시 hit 시엔 create_cached_generation으로 별도 행을 남겨 감사 로그를 유지한다.
"""

import hashlib
import re
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import ApiUsage, Generation, Profile

_WHITESPACE_RE = re.compile(r"\s+")

# 프로필 권한으로 허용되는 값. DB의 CHECK 제약(ck_profiles_role)과 반드시 일치시킨다.
VALID_ROLES = ("user", "admin")


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
    user_id: str | None = None,
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
        user_id: 요청한 로그인 사용자의 UUID(비로그인이면 None).
    Returns:
        새로 만들어진 pending Generation 행.
    """
    generation = Generation(
        request_id=request_id,
        user_id=user_id,
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
    user_id: str | None = None,
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
        user_id: 이번 캐시 hit을 요청한 로그인 사용자의 UUID(비로그인이면 None).
    Returns:
        새로 만들어진 cached Generation 행.
    """
    generation = Generation(
        request_id=request_id,
        user_id=user_id,
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


async def get_profile(db: AsyncSession, user_id: str) -> Profile | None:
    """유저 UUID로 프로필 1건을 조회한다.

    Args:
        db: 활성 DB 세션.
        user_id: Supabase 유저 UUID(JWT sub).
    Returns:
        Profile 행 또는 없으면 None.
    """
    result = await db.execute(select(Profile).where(Profile.id == user_id))
    return result.scalar_one_or_none()


async def upsert_profile(
    db: AsyncSession,
    *,
    user_id: str,
    email: str | None = None,
    display_name: str | None = None,
) -> Profile:
    """프로필을 없으면 role='user'로 생성하고, 있으면 이메일/이름만 갱신한다(원자적 upsert).

    첫 로그인 시 자동 프로필 생성을 담당한다. role은 여기서 건드리지 않아
    관리자 승격 값이 덮어써지지 않는다.

    동시성 주의: 신규 유저의 첫 요청이 동시에 2개 들어오면 select→insert 방식은
    같은 PK로 둘 다 insert를 시도해 충돌(500)이 날 수 있다. 이를 막기 위해 Postgres에서는
    INSERT ... ON CONFLICT로 DB가 한 번에 원자적으로 처리한다. SQLite는 쓰기가 직렬화되어
    경쟁이 없으므로 기존 select→insert 경로를 그대로 쓴다.

    Args:
        db: 활성 DB 세션.
        user_id: Supabase 유저 UUID(JWT sub).
        email: 토큰에서 받은 이메일(있으면 갱신).
        display_name: 표시 이름(있으면 갱신).
    Returns:
        생성 또는 갱신된 Profile 행.
    """
    dialect = db.get_bind().dialect.name

    if dialect == "postgresql":
        # 신규면 role='user'로 insert, 이미 있으면 role은 보존하고 메타데이터만 갱신.
        stmt = pg_insert(Profile).values(
            id=user_id, email=email, display_name=display_name, role="user"
        )
        updates: dict[str, object] = {}
        if email is not None:
            updates["email"] = stmt.excluded.email
        if display_name is not None:
            updates["display_name"] = stmt.excluded.display_name
        if updates:
            stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=updates)
        else:
            # 갱신할 메타데이터가 없으면 충돌 시 아무것도 하지 않는다(기존 행 보존).
            stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        await db.execute(stmt)
        # ON CONFLICT 직후 행은 반드시 존재한다.
        profile = await get_profile(db, user_id)
        assert profile is not None  # noqa: S101 - upsert 직후 불변식 보장.
        return profile

    # SQLite 등: 쓰기가 직렬화되어 동시 경쟁이 없으므로 select→insert로 충분하다.
    profile = await get_profile(db, user_id)
    if profile is None:
        profile = Profile(id=user_id, email=email, display_name=display_name, role="user")
        db.add(profile)
        return profile

    if email is not None:
        profile.email = email
    if display_name is not None:
        profile.display_name = display_name
    return profile


async def set_profile_role(db: AsyncSession, user_id: str, role: str) -> Profile | None:
    """프로필의 권한(role)을 변경한다 (관리자 승격/강등용).

    DB의 CHECK 제약에 닿기 전에 앱 레벨에서도 허용값을 검증해, 잘못된 role이
    의도치 않게 들어오는 것을 명확한 에러로 막는다(2겹 방어).

    Args:
        db: 활성 DB 세션.
        user_id: 대상 유저 UUID.
        role: 새 권한 값('user' 또는 'admin').
    Returns:
        변경된 Profile 행, 대상이 없으면 None.
    Raises:
        ValueError: role이 허용값(user/admin)이 아닐 때.
    """
    if role not in VALID_ROLES:
        raise ValueError(f"허용되지 않은 role입니다: {role!r} (가능: {VALID_ROLES})")
    profile = await get_profile(db, user_id)
    if profile is None:
        return None
    profile.role = role
    return profile


async def list_user_generations(
    db: AsyncSession, user_id: str, *, limit: int = 50
) -> list[Generation]:
    """특정 사용자가 만든 생성 기록을 최신순으로 조회한다 ("내 작업 기록").

    Args:
        db: 활성 DB 세션.
        user_id: 조회할 사용자의 UUID.
        limit: 최대 반환 개수(기본 50).
    Returns:
        최신순으로 정렬된 Generation 리스트(없으면 빈 리스트).
    """
    stmt = (
        select(Generation)
        .where(Generation.user_id == user_id)
        .order_by(Generation.created_at.desc(), Generation.id.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
