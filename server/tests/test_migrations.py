import asyncio

from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import func, select

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.models import Base, Issue
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


def test_seed_rerun_keeps_changes_made_in_the_app(migrated_database):
    async def change_data_then_reseed() -> Issue:
        await seed_database(settings.seed_path)
        async with SessionLocal() as session, session.begin():
            seeded_issue = await session.get(Issue, "i5")
            seeded_issue.solved_at = settings.app_now
            seeded_issue.resolution_note = "Solved in the app"
            session.add(
                Issue(
                    id="app_issue",
                    team_id=seeded_issue.team_id,
                    title=seeded_issue.title,
                    owner_id=seeded_issue.owner_id,
                    source_measurable_id=seeded_issue.source_measurable_id,
                    source_week_start=seeded_issue.source_week_start,
                )
            )
        await seed_database(settings.seed_path)
        async with SessionLocal() as session, session.begin():
            reseeded_issue = await session.get(Issue, "i5")
            await session.delete(await session.get(Issue, "app_issue"))
        await engine.dispose()
        return reseeded_issue

    reseeded_issue = asyncio.run(change_data_then_reseed())
    assert reseeded_issue.resolution_note == "Solved in the app"
