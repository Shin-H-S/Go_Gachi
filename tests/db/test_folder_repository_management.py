import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import crud
from backend.app.db.repositories import folders as folder_repo

pytestmark = pytest.mark.anyio


async def test_folder_rename_and_delete_are_limited_to_owner_and_unassign_generations(
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
        request_id="rename-delete-target",
        image_hash="image-rename-delete",
        preset_id="instagram",
        instruction_hash="instruction-rename-delete",
        prompt_version="prompt-v-test",
        model="model-test",
        original_path=None,
        prompt=None,
        user_id="user-1",
    )
    await folder_repo.set_generation_folder(
        db_session,
        user_id="user-1",
        request_id=generation.request_id,
        folder_id=own_folder.id,
    )

    rejected_rename = await folder_repo.rename_folder(
        db_session,
        user_id="user-1",
        folder_id=other_folder.id,
        name="Hacked",
    )
    renamed = await folder_repo.rename_folder(
        db_session,
        user_id="user-1",
        folder_id=own_folder.id,
        name=" Updated menu ",
    )
    deleted = await folder_repo.delete_folder(
        db_session,
        user_id="user-1",
        folder_id=own_folder.id,
    )
    remaining_generation = await crud.get_user_generation_by_request_id(
        db_session,
        user_id="user-1",
        request_id=generation.request_id,
    )
    rejected_delete = await folder_repo.delete_folder(
        db_session,
        user_id="user-1",
        folder_id=other_folder.id,
    )

    assert rejected_rename is None
    assert renamed is not None
    assert renamed.name == "Updated menu"
    assert deleted is True
    assert remaining_generation is not None
    assert remaining_generation.folder_id is None
    assert rejected_delete is False
