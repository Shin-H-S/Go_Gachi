"""DB CRUD 헬퍼 함수 단위 테스트.

각 테스트는 메모리 SQLite에서 새 DB로 시작해, 테스트가 끝나면 테이블을 모두 비운다.
실제 OpenAI 호출은 일어나지 않는다(파일 I/O는 임시 폴더만 사용).
"""

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db import crud
from backend.app.db.database import Base

pytestmark = pytest.mark.anyio


@pytest.fixture()
async def db_session() -> AsyncSession:
    """테스트용 메모리 SQLite 세션을 만들어준다.

    실제 파일 DB를 안 만들어서 빠르고, 테스트 사이에 데이터가 섞이지 않는다.
    종료 시 세션을 닫고 모든 테이블을 비워 다음 테스트와 격리한다.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_local = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_local() as db:
        yield db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
def tmp_dir() -> Iterator[Path]:
    """테스트용 임시 폴더(컨텍스트 종료 시 자동 삭제)를 제공한다."""
    with tempfile.TemporaryDirectory() as name:
        yield Path(name)


def test_image_sha256_is_stable() -> None:
    """같은 바이트는 같은 해시, 다른 바이트는 다른 해시여야 한다."""
    first = crud.image_sha256(b"same-image")
    second = crud.image_sha256(b"same-image")
    different = crud.image_sha256(b"different-image")

    assert first == second
    assert first != different
    assert len(first) == 64


def test_normalize_instruction_collapses_blank_inputs() -> None:
    """None·빈 문자열·공백만 있는 입력은 모두 ``""``로 통일된다."""
    assert crud.normalize_instruction(None) == ""
    assert crud.normalize_instruction("") == ""
    assert crud.normalize_instruction("   ") == ""
    assert crud.normalize_instruction("\n\t  \n") == ""


def test_normalize_instruction_compacts_whitespace() -> None:
    """앞뒤 공백 제거 + 연속 공백/줄바꿈은 한 칸으로 압축."""
    assert crud.normalize_instruction("  hello   world  ") == "hello world"
    assert crud.normalize_instruction("a\n\nb\t c") == "a b c"


def test_instruction_sha256_is_stable_for_blank_inputs() -> None:
    """빈 지시문은 None/""/공백 모두 동일한 단일 해시를 갖는다."""
    empty = crud.instruction_sha256("")
    none_hash = crud.instruction_sha256(None)
    blanks = crud.instruction_sha256("   \n  ")

    assert empty == none_hash == blanks
    assert len(empty) == 64


def test_instruction_sha256_differs_for_distinct_text() -> None:
    """정규화 결과가 다르면 해시도 달라야 한다."""
    a = crud.instruction_sha256("밝게 해주세요")
    b = crud.instruction_sha256("어둡게 해주세요")

    assert a != b


async def test_find_cached_generation_returns_success_with_existing_file(
    db_session: AsyncSession,
    tmp_dir: Path,
) -> None:
    """성공 기록이 있고 결과 파일도 실제 존재하면 캐시 히트로 같은 기록을 반환한다."""
    output_file = tmp_dir / "result.png"
    output_file.write_bytes(b"png")

    generation = await crud.create_pending_generation(
        db_session,
        request_id="req-1",
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=crud.instruction_sha256(""),
        prompt_version="v1",
        model="gpt-image-2",
        original_path=str(tmp_dir / "input.png"),
        prompt="prompt",
    )
    generation = await crud.mark_generation_success(
        db_session,
        request_id="req-1",
        output_path=str(output_file),
        image_url="/outputs/result.png",
    )
    await db_session.commit()

    cached = await crud.find_cached_generation(
        db_session,
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=crud.instruction_sha256(""),
        prompt_version="v1",
        model="gpt-image-2",
    )

    assert cached is not None
    assert cached.id == generation.id
    assert cached.image_url == "/outputs/result.png"


async def test_find_cached_generation_misses_on_different_instruction(
    db_session: AsyncSession,
    tmp_dir: Path,
) -> None:
    """같은 사진·프리셋이라도 instruction_hash가 다르면 캐시 miss."""
    output_file = tmp_dir / "result.png"
    output_file.write_bytes(b"png")

    await crud.create_pending_generation(
        db_session,
        request_id="req-1",
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=crud.instruction_sha256("밝게"),
        prompt_version="v1",
        model="gpt-image-2",
        original_path=None,
        prompt="prompt-a",
    )
    await crud.mark_generation_success(
        db_session,
        request_id="req-1",
        output_path=str(output_file),
        image_url="/outputs/result.png",
    )
    await db_session.commit()

    # 다른 feedback → 다른 instruction_hash → 캐시 매칭 안 돼야 함
    cached = await crud.find_cached_generation(
        db_session,
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=crud.instruction_sha256("어둡게"),
        prompt_version="v1",
        model="gpt-image-2",
    )

    assert cached is None


async def test_find_cached_generation_ignores_failed_and_missing_files(
    db_session: AsyncSession,
    tmp_dir: Path,
) -> None:
    """실패 기록과 파일이 누락된 성공 기록은 캐시 후보가 되면 안 된다."""
    missing_file = tmp_dir / "missing.png"
    instr_hash = crud.instruction_sha256("")

    await crud.create_pending_generation(
        db_session,
        request_id="req-failed",
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=instr_hash,
        prompt_version="v1",
        model="gpt-image-2",
        original_path=None,
        prompt="prompt",
    )
    await crud.mark_generation_failed(
        db_session,
        request_id="req-failed",
        error_message="openai error",
    )
    await crud.create_pending_generation(
        db_session,
        request_id="req-missing",
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=instr_hash,
        prompt_version="v1",
        model="gpt-image-2",
        original_path=None,
        prompt="prompt",
    )
    await crud.mark_generation_success(
        db_session,
        request_id="req-missing",
        output_path=str(missing_file),
        image_url="/outputs/missing.png",
    )
    await db_session.commit()

    cached = await crud.find_cached_generation(
        db_session,
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=instr_hash,
        prompt_version="v1",
        model="gpt-image-2",
    )

    assert cached is None


async def test_find_cached_generation_falls_back_to_existing_file(
    db_session: AsyncSession,
    tmp_dir: Path,
) -> None:
    """최신 기록 파일이 없으면, 그 이전 기록 중 파일이 있는 것으로 fallback."""
    older_output = tmp_dir / "older.png"
    older_output.write_bytes(b"png")
    missing_output = tmp_dir / "newer-missing.png"
    instr_hash = crud.instruction_sha256("")

    await crud.create_pending_generation(
        db_session,
        request_id="req-older",
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=instr_hash,
        prompt_version="v1",
        model="gpt-image-2",
        original_path=None,
        prompt="older prompt",
    )
    await crud.mark_generation_success(
        db_session,
        request_id="req-older",
        output_path=str(older_output),
        image_url="/outputs/older.png",
    )
    await crud.create_pending_generation(
        db_session,
        request_id="req-newer",
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=instr_hash,
        prompt_version="v1",
        model="gpt-image-2",
        original_path=None,
        prompt="newer prompt",
    )
    await crud.mark_generation_success(
        db_session,
        request_id="req-newer",
        output_path=str(missing_output),
        image_url="/outputs/newer-missing.png",
    )
    await db_session.commit()

    cached = await crud.find_cached_generation(
        db_session,
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=instr_hash,
        prompt_version="v1",
        model="gpt-image-2",
    )

    assert cached is not None
    assert cached.request_id == "req-older"


async def test_create_cached_generation_and_usage_summary(
    db_session: AsyncSession,
    tmp_dir: Path,
) -> None:
    """캐시 hit 기록 생성과 사용량 요약 집계가 의도대로 동작."""
    output_file = tmp_dir / "result.png"
    output_file.write_bytes(b"png")
    instr_hash = crud.instruction_sha256("")

    base_generation = await crud.create_pending_generation(
        db_session,
        request_id="req-1",
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=instr_hash,
        prompt_version="v1",
        model="gpt-image-2",
        original_path=None,
        prompt="prompt",
    )
    base_generation = await crud.mark_generation_success(
        db_session,
        request_id="req-1",
        output_path=str(output_file),
        image_url="/outputs/result.png",
    )
    await crud.record_usage(
        db_session,
        request_id="req-1",
        model="gpt-image-2",
        operation="image_edit",
        estimated_cost=0.01,
        cached=False,
    )
    cached_generation = await crud.create_cached_generation(
        db_session,
        request_id="req-2",
        image_hash=base_generation.image_hash,
        preset_id=base_generation.preset_id,
        instruction_hash=base_generation.instruction_hash,
        prompt_version=base_generation.prompt_version,
        model=base_generation.model,
        original_path=base_generation.original_path,
        output_path=base_generation.output_path,
        image_url=base_generation.image_url,
        prompt=base_generation.prompt,
    )
    await crud.record_usage(
        db_session,
        request_id="req-2",
        model="gpt-image-2",
        operation="image_edit",
        estimated_cost=0.0,
        cached=True,
    )
    await db_session.commit()

    summary = await crud.usage_summary(db_session)

    assert cached_generation.status == "cached"
    assert cached_generation.output_path == str(output_file)
    assert cached_generation.instruction_hash == instr_hash
    assert summary["total_estimated_cost"] == 0.01
    assert summary["generation_count"] == 2
    assert summary["cached_count"] == 1
