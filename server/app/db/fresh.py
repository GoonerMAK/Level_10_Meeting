import asyncio
import sys

import asyncpg
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import SERVER_ROOT, settings
from app.seed import seed_database


def database_url_named(suffix: str) -> URL:
    url = make_url(settings.database_url)
    return url.set(database=f"{url.database}_{suffix}")


async def run_admin_sql(url: URL, statement: str) -> None:
    admin_url = url.set(drivername="postgresql", database="postgres")
    connection = await asyncpg.connect(admin_url.render_as_string(hide_password=False))
    try:
        await connection.execute(statement)
    finally:
        await connection.close()


def migrate(url: URL) -> None:
    config = Config(str(SERVER_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False).replace("%", "%%"))
    command.upgrade(config, "head")


async def drop_database(url: URL) -> None:
    await run_admin_sql(url, f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)')


def session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_seeded_database(url: URL) -> None:
    await drop_database(url)
    await run_admin_sql(url, f'CREATE DATABASE "{url.database}"')
    await asyncio.to_thread(migrate, url)
    engine = create_async_engine(url)
    try:
        await seed_database(settings.seed_path, session_maker(engine))
    finally:
        await engine.dispose()


def main() -> None:
    url = database_url_named(sys.argv[1])
    asyncio.run(create_seeded_database(url))
    print(url.render_as_string(hide_password=False))


if __name__ == "__main__":
    main()
