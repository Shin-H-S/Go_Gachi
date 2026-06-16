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
