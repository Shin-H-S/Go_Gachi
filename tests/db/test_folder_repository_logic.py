import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import crud
from backend.app.db.repositories import folders as folder_repo

pytestmark = pytest.mark.anyio


async def test_generation_folder_assignment_is_limited_to_same_user(
    db_session: AsyncSession,
) -> None:
    own_folder = await folder_repo.create_folder(
        db_session,
        user_id="user-1",
        name=" Spring menu ",
    )
    other_folder = await folder_repo.create_folder(
        db_session,
        user_id="user-2",
        name="Other user folder",
    )
    generation = await crud.create_pending_generation(
        db_session,
        request_id="request-1",
        image_hash="image-1",
        preset_id="instagram",
        instruction_hash="instruction-1",
        prompt_version="prompt-v-test",
        model="model-test",
        original_path=None,
        prompt=None,
        user_id="user-1",
    )

    rejected = await folder_repo.set_generation_folder(
        db_session,
        user_id="user-1",
        request_id=generation.request_id,
        folder_id=other_folder.id,
    )
    assigned = await folder_repo.set_generation_folder(
        db_session,
        user_id="user-1",
        request_id=generation.request_id,
        folder_id=own_folder.id,
    )
    assigned_folder_id = assigned.folder_id if assigned is not None else None
    unassigned = await folder_repo.set_generation_folder(
        db_session,
        user_id="user-1",
        request_id=generation.request_id,
        folder_id=None,
    )

    assert own_folder.name == "Spring menu"
    assert rejected is None
    assert assigned is not None
    assert assigned_folder_id == own_folder.id
    assert unassigned is not None
    assert unassigned.folder_id is None


async def test_folder_creation_rejects_empty_and_long_names(
    db_session: AsyncSession,
) -> None:
    with pytest.raises(ValueError):
        await folder_repo.create_folder(db_session, user_id="user-1", name="   ")

    with pytest.raises(ValueError):
        await folder_repo.create_folder(db_session, user_id="user-1", name="x" * 81)


async def test_list_user_generations_supports_limit_offset_and_total(
    db_session: AsyncSession,
) -> None:
    for idx in range(12):
        await crud.create_pending_generation(
            db_session,
            request_id=f"page-{idx:02d}",
            image_hash=f"hash-page-{idx:02d}",
            preset_id="instagram",
            instruction_hash=f"instruction-page-{idx:02d}",
            prompt_version="prompt-v-test",
            model="model-test",
            original_path=None,
            prompt=None,
            user_id="user-page",
        )
    await crud.create_pending_generation(
        db_session,
        request_id="other-user-page",
        image_hash="hash-other-page",
        preset_id="instagram",
        instruction_hash="instruction-other-page",
        prompt_version="prompt-v-test",
        model="model-test",
        original_path=None,
        prompt=None,
        user_id="other-user",
    )

    first = await folder_repo.list_user_generations(db_session, "user-page", limit=10, offset=0)
    second = await folder_repo.list_user_generations(db_session, "user-page", limit=10, offset=10)
    empty = await folder_repo.list_user_generations(db_session, "user-page", limit=10, offset=20)
    total = await folder_repo.count_user_generations(db_session, "user-page")

    assert [row.request_id for row in first] == [f"page-{idx:02d}" for idx in range(11, 1, -1)]
    assert [row.request_id for row in second] == ["page-01", "page-00"]
    assert empty == []
    assert total == 12


async def test_folder_and_upload_lists_are_scoped_to_user(
    db_session: AsyncSession,
) -> None:
    own_folder = await folder_repo.create_folder(
        db_session,
        user_id="user-1",
        name="Own folder",
    )
    await folder_repo.create_folder(
        db_session,
        user_id="user-2",
        name="Other folder",
    )
    await crud.create_pending_generation(
        db_session,
        request_id="own-upload",
        image_hash="hash-own-upload",
        preset_id="instagram",
        instruction_hash="instruction-own-upload",
        prompt_version="prompt-v-test",
        model="model-test",
        original_path="uploads/own.png",
        prompt=None,
        user_id="user-1",
    )
    await crud.create_pending_generation(
        db_session,
        request_id="own-generated-only",
        image_hash="hash-own-generated",
        preset_id="instagram",
        instruction_hash="instruction-own-generated",
        prompt_version="prompt-v-test",
        model="model-test",
        original_path=None,
        prompt=None,
        user_id="user-1",
    )
    await crud.create_pending_generation(
        db_session,
        request_id="other-upload",
        image_hash="hash-other-upload",
        preset_id="instagram",
        instruction_hash="instruction-other-upload",
        prompt_version="prompt-v-test",
        model="model-test",
        original_path="uploads/other.png",
        prompt=None,
        user_id="user-2",
    )

    folders = await folder_repo.list_user_folders(db_session, "user-1")
    uploads = await folder_repo.list_user_upload_generations(db_session, "user-1")

    assert [folder.id for folder in folders] == [own_folder.id]
    assert [row.request_id for row in uploads] == ["own-upload"]
