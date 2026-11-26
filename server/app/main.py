import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.core.errors import register_error_handlers
from app.db.session import engine
from app.modules.auth.router import router as auth_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    async with engine.connect() as connection:
        server_version = await connection.scalar(text("SHOW server_version"))
    logger.info("Database connection established (PostgreSQL %s)", server_version)
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(title="Level 10 Meeting API", lifespan=lifespan)
register_error_handlers(app)
app.include_router(auth_router, prefix="/api")
