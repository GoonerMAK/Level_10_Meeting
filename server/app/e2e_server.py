import asyncio
import os
import subprocess
import sys

from sqlalchemy.engine import URL, make_url

from app.core.config import SERVER_ROOT, settings
from app.db.fresh import seeded_database

DEFAULT_PORT = "8100"


def e2e_database_url() -> URL:
    url = make_url(settings.database_url)
    return url.set(database=f"{url.database}_e2e")


async def rebuild(url: URL) -> None:
    async with seeded_database(url):
        return


def main() -> None:
    url = e2e_database_url()
    asyncio.run(rebuild(url))
    port = os.environ.get("E2E_API_PORT", DEFAULT_PORT)
    env = {**os.environ, "DATABASE_URL": url.render_as_string(hide_password=False)}
    command = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", port]
    sys.exit(subprocess.call(command, cwd=SERVER_ROOT, env=env))


if __name__ == "__main__":
    main()
