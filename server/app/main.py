import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.errors import register_error_handlers
from app.db.session import engine
from app.modules.auth.router import router as auth_router
from app.modules.auth.service import SIGN_IN_IDLE_SECONDS
from app.modules.issues.router import router as issues_router
from app.modules.live.router import router as live_router
from app.modules.rocks.router import router as rocks_router
from app.modules.scorecard.router import router as scorecard_router
from app.modules.teams.router import router as teams_router
from app.modules.todos.router import router as todos_router

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
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret.get_secret_value(), max_age=SIGN_IN_IDLE_SECONDS)
register_error_handlers(app)
for router in (auth_router, teams_router, scorecard_router, issues_router, todos_router, rocks_router, live_router):
    app.include_router(router, prefix="/api")
