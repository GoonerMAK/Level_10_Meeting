import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.models import Base

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata
database_url = context.config.get_main_option("sqlalchemy.url") or settings.database_url


def configure(connection: Connection | None = None) -> None:
    context.configure(
        connection=connection,
        url=None if connection else database_url,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        literal_binds=connection is None,
    )


def run_migrations(connection: Connection | None = None) -> None:
    configure(connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_online() -> None:
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        await connection.run_sync(run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations()
else:
    asyncio.run(run_online())
