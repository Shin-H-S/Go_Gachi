import asyncio
from collections.abc import Iterator

import pytest

from backend.app.db.database import async_init_db, async_session_scope
from backend.app.db.models import ApiUsage, Folder, Generation


@pytest.fixture(autouse=True)
def clean_db() -> Iterator[None]:
    async def _clean() -> None:
        await async_init_db()
        async with async_session_scope() as db:
            await db.execute(Generation.__table__.delete())
            await db.execute(Folder.__table__.delete())
            await db.execute(ApiUsage.__table__.delete())

    asyncio.run(_clean())
    yield
