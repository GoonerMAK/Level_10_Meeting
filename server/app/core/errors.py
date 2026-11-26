from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


class AppError(Exception):
    status_code = HTTPStatus.BAD_REQUEST
    code = "bad_request"

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


def error_response(status_code: int, code: str, message: str, fields: list[dict[str, str]] | None = None) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if fields:
        error["fields"] = fields
    return JSONResponse(status_code=status_code, content={"error": error})


def field_name(location: tuple[str | int, ...]) -> str:
    return ".".join(str(part) for part in location[1:]) or str(location[0])


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, error: AppError) -> JSONResponse:
        return error_response(error.status_code, error.code, error.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_request: Request, error: RequestValidationError) -> JSONResponse:
        fields = [{"field": field_name(item["loc"]), "message": item["msg"]} for item in error.errors()]
        return error_response(HTTPStatus.UNPROCESSABLE_CONTENT, "invalid_input", "Some fields are invalid", fields)

    @app.exception_handler(HTTPException)
    async def handle_http_error(_request: Request, error: HTTPException) -> JSONResponse:
        code = HTTPStatus(error.status_code).phrase.lower().replace(" ", "_")
        return error_response(error.status_code, code, str(error.detail))
