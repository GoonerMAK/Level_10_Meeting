from http import HTTPStatus
from typing import Any

from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: list[FieldError] | None = None


class ErrorBody(BaseModel):
    error: ErrorDetail


def example(code: str, message: str, field: str | None = None) -> dict[str, Any]:
    detail: dict[str, Any] = {"code": code, "message": message}
    if field:
        detail["fields"] = [{"field": field, "message": message}]
    return {"error": detail}


ERROR_DOCS: dict[HTTPStatus, tuple[str, dict[str, Any]]] = {
    HTTPStatus.UNAUTHORIZED: ("Not signed in", example("unauthorized", "Choose a user first")),
    HTTPStatus.FORBIDDEN: (
        "Signed in, but this role can't do this",
        example("forbidden", "Observers can view this team but cannot change anything"),
    ),
    HTTPStatus.NOT_FOUND: ("Not found, or on a team you can't open", example("not_found", "Team not found")),
    HTTPStatus.CONFLICT: ("Clashes with the current data", example("conflict", "This Issue is already solved")),
    HTTPStatus.UNPROCESSABLE_CONTENT: (
        "Some input is invalid; each bad field is listed",
        example("invalid_input", "Priority must be 1 to 5", "priority"),
    ),
}


def error_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    responses: dict[int | str, dict[str, Any]] = {}
    for status in statuses:
        description, body = ERROR_DOCS[HTTPStatus(status)]
        responses[status] = {
            "description": description,
            "model": ErrorBody,
            "content": {"application/json": {"example": body}},
        }
    return responses


FRAMEWORK_ERROR_SCHEMAS = ("HTTPValidationError", "ValidationError")


def without_framework_errors(schema: dict[str, Any]) -> dict[str, Any]:
    for operations in schema["paths"].values():
        for operation in operations.values():
            invalid = operation.get("responses", {}).get("422", {})
            reference = invalid.get("content", {}).get("application/json", {}).get("schema", {}).get("$ref", "")
            if reference.endswith("/HTTPValidationError"):
                del operation["responses"]["422"]
    for name in FRAMEWORK_ERROR_SCHEMAS:
        schema.get("components", {}).get("schemas", {}).pop(name, None)
    return schema
