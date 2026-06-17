from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Folder, Generation


async def list_user_generations(
    db: AsyncSession,
    user_id: str,
    *,
    limit: int = 10,
    offset: int = 0,
    folder_id: int | None = None,
    uncategorized: bool = False,
) -> list[Generation]:
    """현재 사용자의 generation 행 목록을 최신순으로 반환한다.

    folder_id가 주어지면 해당 폴더에 속한 행만 반환한다(폴더별 페이지네이션 지원).
    """
    stmt = (
        select(Generation)
        .where(Generation.user_id == user_id)
        .order_by(Generation.created_at.desc(), Generation.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if uncategorized:
        stmt = stmt.where(Generation.folder_id.is_(None))
    elif folder_id is not None:
        stmt = stmt.where(Generation.folder_id == folder_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def count_user_generations(
    db: AsyncSession,
    user_id: str,
    *,
    folder_id: int | None = None,
    uncategorized: bool = False,
) -> int:
    """현재 사용자의 generation 행 총 개수를 반환한다.

    folder_id가 주어지면 해당 폴더에 속한 행만 센다.
    """
    stmt = select(func.count()).select_from(Generation).where(Generation.user_id == user_id)
    if uncategorized:
        stmt = stmt.where(Generation.folder_id.is_(None))
    elif folder_id is not None:
        stmt = stmt.where(Generation.folder_id == folder_id)
    result = await db.execute(stmt)
    return int(result.scalar_one())


def _clean_folder_name(name: str) -> str:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("폴더 이름을 입력해주세요.")
    if len(clean_name) > 80:
        raise ValueError("폴더 이름은 80자 이하로 입력해주세요.")
    return clean_name


async def create_folder(db: AsyncSession, *, user_id: str, name: str) -> Folder:
    clean_name = _clean_folder_name(name)

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


async def rename_folder(
    db: AsyncSession,
    *,
    user_id: str,
    folder_id: int,
    name: str,
) -> Folder | None:
    folder = await get_user_folder(db, user_id, folder_id)
    if folder is None:
        return None

    folder.name = _clean_folder_name(name)
    await db.flush()
    return folder


async def delete_folder(
    db: AsyncSession,
    *,
    user_id: str,
    folder_id: int,
) -> bool:
    folder = await get_user_folder(db, user_id, folder_id)
    if folder is None:
        return False

    await db.execute(
        update(Generation)
        .where(Generation.user_id == user_id)
        .where(Generation.folder_id == folder_id)
        .values(folder_id=None)
    )
    await db.delete(folder)
    await db.flush()
    return True


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
    limit: int = 8,
    offset: int = 0,
) -> list[tuple[Generation, int]]:
    ranked_uploads = (
        select(
            Generation.id.label("generation_id"),
            func.count().over(partition_by=Generation.image_hash).label("used_count"),
            func.row_number()
            .over(
                partition_by=Generation.image_hash,
                order_by=(Generation.created_at.desc(), Generation.id.desc()),
            )
            .label("row_number"),
        )
        .where(Generation.user_id == user_id)
        .where(Generation.original_path.is_not(None))
        .subquery()
    )
    stmt = (
        select(Generation, ranked_uploads.c.used_count)
        .join(ranked_uploads, ranked_uploads.c.generation_id == Generation.id)
        .where(ranked_uploads.c.row_number == 1)
        .order_by(Generation.created_at.desc(), Generation.id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return [(row[0], int(row[1])) for row in result.all()]


async def count_user_upload_generations(
    db: AsyncSession,
    user_id: str,
) -> int:
    unique_uploads = (
        select(Generation.image_hash)
        .where(Generation.user_id == user_id)
        .where(Generation.original_path.is_not(None))
        .group_by(Generation.image_hash)
        .subquery()
    )
    result = await db.execute(select(func.count()).select_from(unique_uploads))
    return int(result.scalar_one())
