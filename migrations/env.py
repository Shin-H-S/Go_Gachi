"""Alembic 마이그레이션 진입점.

우리 앱의 Settings(.env)에서 DATABASE_URL을 받아 asyncpg로 연결하고,
Base.metadata를 기준으로 자동 생성(autogenerate)을 수행한다.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# 우리 앱 설정과 ORM 메타데이터 import. URL 변환은 database 모듈의 함수를 그대로 재사용해
# 동기 URL → async 드라이버 URL 보정 로직이 한 곳에서만 유지되도록 한다.
from backend.app.core.config import get_settings
from backend.app.db import models  # noqa: F401  (모델 등록 위해 import)
from backend.app.db.database import Base, _async_database_url, _connect_args

config = context.config

# alembic.ini의 [alembic] 섹션 sqlalchemy.url 자리에 우리 .env DATABASE_URL을 동적으로 주입.
settings = get_settings()
_database_url = _async_database_url(settings.database_url)
# configparser가 '%'를 변수 보간자로 해석하지 않게 이중으로 이스케이프한다.
config.set_main_option("sqlalchemy.url", _database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# autogenerate가 ORM 모델과 DB 상태를 비교할 기준.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 모드: 실제 DB 없이 SQL 스크립트만 생성한다."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """async 연결 위에서 동기 마이그레이션 함수를 호출하는 어댑터."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """비동기 엔진을 만들어 마이그레이션을 적용한다."""
    # Transaction pooler(6543, pgbouncer)에서도 prepared statement 에러가 나지 않도록
    # 앱 엔진과 동일하게 statement 캐시를 끈다(_connect_args 재사용).
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=_connect_args(_database_url),
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """온라인 모드: 실제 DB에 연결해서 마이그레이션을 적용한다."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
