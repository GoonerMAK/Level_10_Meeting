import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.db.session import engine

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    async with engine.connect() as connection:
        server_version = await connection.scalar(text("SHOW server_version"))
    logger.info("Database connection established (PostgreSQL %s)", server_version)
    yield
    await engine.dispose()

app = FastAPI(title="Level 10 Meeting API", lifespan=lifespan)
