from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from asyncpg.exceptions import ForeignKeyViolationError, NotNullViolationError
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException

from app.core.logs import REQUEST_ID_HEADER, logger
from app.core.messages import DATA_RULES, FIELD_MESSAGES, UNKNOWN_LINK, UNKNOWN_RULE, DataRule, bad_value


class AppError(Exception):
    status_code = HTTPStatus.BAD_REQUEST
    code = "bad_request"
    fields: list[dict[str, str]] | None = None

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class Unauthorized(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "unauthorized"


class Forbidden(AppError):
    status_code = HTTPStatus.FORBIDDEN
    code = "forbidden"


class NotFound(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "not_found"


class Conflict(AppError):
    status_code = HTTPStatus.CONFLICT
    code = "conflict"


class InvalidInput(AppError):
    status_code = HTTPStatus.UNPROCESSABLE_CONTENT
    code = "invalid_input"

    def __init__(self, message: str, field: str) -> None:
        super().__init__(message)
        self.fields = [{"field": field, "message": message}]


def error_response(
    status_code: int,
    code: str,
    message: str,
    fields: list[dict[str, str]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return JSONResponse(status_code=status_code, content={"error": error}, headers=headers)


def field_name(location: tuple[str | int, ...]) -> str:
    return ".".join(str(part) for part in location[1:]) or str(location[0])


def plain_fields(error: RequestValidationError) -> list[dict[str, str]]:
    fields: dict[str, str] = {}
    for item in error.errors():
        field = field_name(item["loc"])
        fields.setdefault(field, FIELD_MESSAGES.get(field, item["msg"]))
    return [{"field": field, "message": message} for field, message in fields.items()]


def broken_data_rule(error: IntegrityError) -> DataRule:
    cause = error.orig.__cause__ if error.orig is not None else None
    constraint = getattr(cause, "constraint_name", None)
    if constraint in DATA_RULES:
        return DATA_RULES[constraint]
    if isinstance(cause, NotNullViolationError):
        column = cause.column_name
        return bad_value(FIELD_MESSAGES.get(column, "A required value is missing"), column)
    if isinstance(cause, ForeignKeyViolationError):
        return UNKNOWN_LINK
    logger.warning("No plain message for database rule %s", constraint or type(cause).__name__)
    return UNKNOWN_RULE


def remember_error_code(request: Request, code: str) -> None:
    request.state.error_code = code


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, error: AppError) -> JSONResponse:
        remember_error_code(request, error.code)
        return error_response(error.status_code, error.code, error.message, error.fields)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        remember_error_code(request, "invalid_input")
        fields = plain_fields(error)
        message = fields[0]["message"] if len(fields) == 1 else "Some fields are invalid"
        return error_response(HTTPStatus.UNPROCESSABLE_CONTENT, "invalid_input", message, fields)

    @app.exception_handler(IntegrityError)
    async def handle_broken_data_rule(request: Request, error: IntegrityError) -> JSONResponse:
        rule = broken_data_rule(error)
        code = "conflict" if rule.status is HTTPStatus.CONFLICT else "invalid_input"
        remember_error_code(request, code)
        fields = [{"field": rule.field, "message": rule.message}] if rule.field else None
        return error_response(rule.status, code, rule.message, fields)

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, error: HTTPException) -> JSONResponse:
        code = HTTPStatus(error.status_code).phrase.lower().replace(" ", "_")
        remember_error_code(request, code)
        return error_response(error.status_code, code, str(error.detail), headers=error.headers)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _error: Exception) -> JSONResponse:
        current_id = getattr(request.state, "request_id", None)
        headers = {REQUEST_ID_HEADER: current_id} if current_id else None
        return error_response(
            HTTPStatus.INTERNAL_SERVER_ERROR, "internal_error", "Something went wrong on the server", headers=headers
        )
