import asyncio
import os
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

import asyncpg
import pytest
from dotenv import dotenv_values
from sqlalchemy.engine import make_url

TEST_DATABASE_NAME = "level10_test"
SERVER_DIR = Path(__file__).resolve().parents[1]
REPO_ENV_FILE = SERVER_DIR.parent / ".env"


def dev_database_url() -> str:
    return os.environ.get("DATABASE_URL") or dotenv_values(REPO_ENV_FILE)["DATABASE_URL"]


TEST_DATABASE_URL = make_url(dev_database_url()).set(database=TEST_DATABASE_NAME)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL.render_as_string(hide_password=False)
os.environ.setdefault("SESSION_SECRET", "test-session-secret")


async def recreate_test_database() -> None:
    admin_url = TEST_DATABASE_URL.set(drivername="postgresql", database="postgres")
    connection = await asyncpg.connect(admin_url.render_as_string(hide_password=False))
    try:
        await connection.execute(f"DROP DATABASE IF EXISTS {TEST_DATABASE_NAME} WITH (FORCE)")
        await connection.execute(f"CREATE DATABASE {TEST_DATABASE_NAME}")
    finally:
        await connection.close()


@pytest.fixture(scope="session")
def alembic_config():
    from alembic.config import Config

    return Config(str(SERVER_DIR / "alembic.ini"))


@pytest.fixture(scope="session")
def migrated_database(alembic_config):
    from alembic import command

    asyncio.run(recreate_test_database())
    command.upgrade(alembic_config, "head")


@pytest.fixture(scope="session")
def seeded_database(migrated_database):
    from app.core.config import settings
    from app.db.session import engine
    from app.seed import seed_database

    async def seed() -> None:
        await seed_database(settings.seed_path)
        await engine.dispose()

    asyncio.run(seed())


@pytest.fixture
def client(seeded_database):
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sign_in(client):
    def sign_in_as(user_id):
        response = client.post("/api/auth/sign-in", json={"user_id": user_id})
        assert response.status_code == 200
        return client

    return sign_in_as


@pytest.fixture
def signed_in_clients(seeded_database):
    import httpx2

    from app.main import app

    @asynccontextmanager
    async def open_clients(*user_ids):
        async with AsyncExitStack() as stack:
            clients = {}
            for user_id in user_ids:
                transport = httpx2.ASGITransport(app=app)
                client = await stack.enter_async_context(httpx2.AsyncClient(transport=transport, base_url="http://test"))
                response = await client.post("/api/auth/sign-in", json={"user_id": user_id})
                assert response.status_code == 200
                clients[user_id] = client
            yield clients

    return open_clients
