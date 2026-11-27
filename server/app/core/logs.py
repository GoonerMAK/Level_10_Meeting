import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "x-request-id"
INCOMING_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{8,64}")

logger = logging.getLogger("level10")
request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "request_id": request_id.get(),
            **getattr(record, "fields", {}),
        }
        if record.exc_info:
            entry["error"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.handlers = [handler]
    logger.setLevel(level.upper())
    logger.propagate = False


def chosen_request_id(scope: Scope) -> str:
    incoming = Headers(scope=scope).get(REQUEST_ID_HEADER, "")
    return incoming if INCOMING_REQUEST_ID.fullmatch(incoming) else uuid4().hex


class RequestLog:
    def __init__(self, app: ASGIApp, slow_after_ms: int) -> None:
        self.app = app
        self.slow_after_ms = slow_after_ms

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        current_id = chosen_request_id(scope)
        scope.setdefault("state", {})["request_id"] = current_id
        token = request_id.set(current_id)
        started = perf_counter()
        status = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                MutableHeaders(scope=message).append(REQUEST_ID_HEADER, current_id)
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            self.log(scope, 500, started, crashed=True)
            raise
        else:
            self.log(scope, status, started)
        finally:
            request_id.reset(token)

    def log(self, scope: Scope, status: int, started: float, crashed: bool = False) -> None:
        duration_ms = round((perf_counter() - started) * 1000, 1)
        slow = duration_ms >= self.slow_after_ms
        if status < 400 and not slow:
            return
        fields = {
            "method": scope["method"],
            "path": scope["path"],
            "status": status,
            "duration_ms": duration_ms,
            "user_id": (scope.get("session") or {}).get("user_id"),
            "error_code": (scope.get("state") or {}).get("error_code"),
        }
        level = logging.ERROR if status >= 500 else logging.WARNING if slow else logging.INFO
        if crashed:
            message = "Request crashed"
        elif status >= 500:
            message = "Request failed"
        elif status >= 400:
            message = "Request refused"
        else:
            message = "Slow request"
        logger.log(level, message, exc_info=crashed, extra={"fields": fields})
