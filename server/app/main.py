import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

from app.core.clock import TickingClock, use_clock
from app.core.config import settings
from app.core.error_docs import without_framework_errors
from app.core.logs import RequestLog, configure_logging
from app.core.errors import register_error_handlers
from app.db.clock import keep_saving_app_time, load_app_time, save_app_time
from app.db.session import engine
from app.modules.activity.router import router as activity_router
from app.modules.auth.router import router as auth_router
from app.modules.auth.service import SIGN_IN_IDLE_SECONDS
from app.modules.issues.router import router as issues_router
from app.modules.live.router import router as live_router
from app.modules.meetings.router import router as meetings_router
from app.modules.meetings.service import keep_ending_empty_meetings
from app.modules.rocks.router import router as rocks_router
from app.modules.scorecard.router import router as scorecard_router
from app.modules.teams.router import router as teams_router
from app.modules.todos.router import router as todos_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    async with engine.connect() as connection:
        server_version = await connection.scalar(text("SHOW server_version"))
        clock = TickingClock(await load_app_time(connection, settings.app_now))
    use_clock(clock)
    logger.info("Database connection established (PostgreSQL %s)", server_version)
    background = [
        asyncio.create_task(keep_saving_app_time(settings.app_now, clock)),
        asyncio.create_task(keep_ending_empty_meetings()),
    ]
    try:
        yield
    finally:
        for task in background:
            task.cancel()
        await asyncio.gather(*background, return_exceptions=True)
        await save_app_time(settings.app_now, clock)
        await engine.dispose()


API_DESCRIPTION = (
    "Every error uses one shape: `{\"error\": {\"code\", \"message\", \"fields\"}}`. "
    "Each route lists the errors it can return.\n\n"
    "The live meeting connection (`/api/live?team_id=...`) is a WebSocket, which this page can't show. "
    "Its messages are described in the README, under "
    "[Live connection](https://github.com/GoonerMAK/Level_10_Meeting#live-connection)."
)

app = FastAPI(title="Level 10 Meeting API", description=API_DESCRIPTION, lifespan=lifespan)
configure_logging(settings.log_level)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret.get_secret_value(), max_age=SIGN_IN_IDLE_SECONDS)
app.add_middleware(RequestLog, slow_after_ms=settings.slow_request_ms)
register_error_handlers(app)

ROUTERS = (
    auth_router,
    teams_router,
    scorecard_router,
    issues_router,
    todos_router,
    rocks_router,
    meetings_router,
    activity_router,
    live_router,
)
for router in ROUTERS:
    app.include_router(router, prefix="/api")


def api_schema() -> dict[str, Any]:
    if app.openapi_schema is None:
        schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        app.openapi_schema = without_framework_errors(schema)
    return app.openapi_schema


app.openapi = api_schema
