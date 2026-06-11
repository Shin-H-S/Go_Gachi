from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import crud

pytestmark = pytest.mark.anyio


async def test_create_cached_generation_and_usage_summary(
    db_session: AsyncSession,
    tmp_dir: Path,
) -> None:
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
    usage = await crud.record_usage(
        db_session,
        request_id="req-1",
        image_model="gpt-image-2",
        text_model="gpt-5.4-mini",
        image_cost_usd=0.01,
        text_cost_usd=0.02,
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
        image_model="gpt-image-2",
        text_model=None,
        image_cost_usd=0.0,
        text_cost_usd=0.0,
        cached=True,
    )
    await db_session.commit()

    summary = await crud.usage_summary(db_session)

    assert cached_generation.status == "cached"
    assert cached_generation.output_path == str(output_file)
    assert cached_generation.instruction_hash == instr_hash
    assert usage.cost_usd == 0.03
    assert summary["total_cost_usd"] == 0.03
    assert summary["generation_count"] == 2
    assert summary["cached_count"] == 1
