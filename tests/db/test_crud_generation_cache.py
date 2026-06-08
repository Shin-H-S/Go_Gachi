from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import crud

pytestmark = pytest.mark.anyio


async def test_find_cached_generation_returns_success_with_existing_file(
    db_session: AsyncSession,
    tmp_dir: Path,
) -> None:
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
    output_file = tmp_dir / "result.png"
    output_file.write_bytes(b"png")

    await crud.create_pending_generation(
        db_session,
        request_id="req-1",
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=crud.instruction_sha256("bright"),
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

    cached = await crud.find_cached_generation(
        db_session,
        image_hash="h1",
        preset_id="instagram_feed_square",
        instruction_hash=crud.instruction_sha256("dark"),
        prompt_version="v1",
        model="gpt-image-2",
    )

    assert cached is None


async def test_find_cached_generation_ignores_failed_and_missing_files(
    db_session: AsyncSession,
    tmp_dir: Path,
) -> None:
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
