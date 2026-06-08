from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Folder, Generation


async def list_user_generations(
    db: AsyncSession, user_id: str, *, limit: int = 50
) -> list[Generation]:
    stmt = (
        select(Generation)
        .where(Generation.user_id == user_id)
        .order_by(Generation.created_at.desc(), Generation.id.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_folder(db: AsyncSession, *, user_id: str, name: str) -> Folder:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("폴더 이름을 입력해주세요.")
    if len(clean_name) > 80:
        raise ValueError("폴더 이름은 80자 이하로 입력해주세요.")

    folder = Folder(user_id=user_id, name=clean_name)
    db.add(folder)
    await db.flush()
    return folder


async def list_user_folders(db: AsyncSession, user_id: str) -> list[Folder]:
    stmt = (
        select(Folder)
        .where(Folder.user_id == user_id)
        .order_by(Folder.created_at.asc(), Folder.id.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_user_folder(db: AsyncSession, user_id: str, folder_id: int) -> Folder | None:
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id).where(Folder.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def set_generation_folder(
    db: AsyncSession,
    *,
    user_id: str,
    request_id: str,
    folder_id: int | None,
) -> Generation | None:
    result = await db.execute(
        select(Generation)
        .where(Generation.request_id == request_id)
        .where(Generation.user_id == user_id)
    )
    generation = result.scalar_one_or_none()
    if generation is None:
        return None

    if folder_id is not None:
        folder = await get_user_folder(db, user_id, folder_id)
        if folder is None:
            return None

    generation.folder_id = folder_id
    await db.flush()
    return generation


async def list_user_upload_generations(
    db: AsyncSession,
    user_id: str,
    *,
    limit: int = 100,
) -> list[Generation]:
    stmt = (
        select(Generation)
        .where(Generation.user_id == user_id)
        .where(Generation.original_path.is_not(None))
        .order_by(Generation.created_at.desc(), Generation.id.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
