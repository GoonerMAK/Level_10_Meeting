import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import SERVER_ROOT, settings
from app.seed import seed_database


async def run_admin_sql(url: URL, statement: str) -> None:
    admin_url = url.set(drivername="postgresql", database="postgres")
    connection = await asyncpg.connect(admin_url.render_as_string(hide_password=False))
    try:
        await connection.execute(statement)
    finally:
        await connection.close()


async def drop_database(url: URL) -> None:
    await run_admin_sql(url, f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)')


def migrate(url: URL) -> None:
    config = Config(str(SERVER_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False).replace("%", "%%"))
    command.upgrade(config, "head")


@asynccontextmanager
async def seeded_database(url: URL) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    await drop_database(url)
    await run_admin_sql(url, f'CREATE DATABASE "{url.database}"')
    engine = create_async_engine(url)
    try:
        await asyncio.to_thread(migrate, url)
        sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        await seed_database(settings.seed_path, sessions)
        yield sessions
    finally:
        await engine.dispose()
