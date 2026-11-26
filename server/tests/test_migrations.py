import asyncio

from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import func, select

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.models import Base
from app.seed import seed_database


def test_migrations_have_a_single_head(alembic_config):
    assert len(ScriptDirectory.from_config(alembic_config).get_heads()) == 1


def test_empty_database_upgrades_to_head(alembic_config, migrated_database):
    head = ScriptDirectory.from_config(alembic_config).get_current_head()

    async def current_revision() -> str | None:
        async with engine.connect() as connection:
            revision = await connection.run_sync(
                lambda sync_connection: MigrationContext.configure(sync_connection).get_current_revision()
            )
        await engine.dispose()
        return revision

    assert asyncio.run(current_revision()) == head


def test_models_match_migrated_database(alembic_config, migrated_database):
    command.check(alembic_config)


def test_seed_loads_and_can_run_again(migrated_database):
    async def seed_twice_and_count() -> tuple[dict[str, int], dict[str, int]]:
        await seed_database(settings.seed_path)
        expected = await seed_database(settings.seed_path)
        async with SessionLocal() as session:
            actual = {
                table.name: await session.scalar(select(func.count()).select_from(table))
                for table in Base.metadata.sorted_tables
                if table.name in expected
            }
        await engine.dispose()
        return expected, actual

    expected, actual = asyncio.run(seed_twice_and_count())
    assert actual == expected
