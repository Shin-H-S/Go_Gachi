from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import Profile

VALID_ROLES = ("user", "admin")


async def get_profile(db: AsyncSession, user_id: str) -> Profile | None:
    result = await db.execute(select(Profile).where(Profile.id == user_id))
    return result.scalar_one_or_none()


async def upsert_profile(
    db: AsyncSession,
    *,
    user_id: str,
    email: str | None = None,
    display_name: str | None = None,
) -> Profile:
    dialect = db.get_bind().dialect.name

    if dialect == "postgresql":
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
            stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
        await db.execute(stmt)
        profile = await get_profile(db, user_id)
        assert profile is not None  # noqa: S101
        return profile

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
    if role not in VALID_ROLES:
        raise ValueError(f"허용되지 않은 role입니다: {role!r} (가능: {VALID_ROLES})")
    profile = await get_profile(db, user_id)
    if profile is None:
        return None
    profile.role = role
    return profile
