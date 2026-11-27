import json
import re
from pathlib import Path

import pytest
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

from app.main import ROUTERS, app
from app.modules.auth.dependencies import get_current_user
from app.modules.live.messages import Changed, Hello, MeetingMessage, live_message

README = Path(__file__).resolve().parents[2] / "README.md"
ERROR_SHAPE = "#/components/schemas/ErrorBody"

API_ROUTES = [route for router in ROUTERS for route in router.routes if isinstance(route, APIRoute)]


def route_id(route):
    return f"{sorted(route.methods)[0]} {route.path}"


def operation(route):
    return app.openapi()["paths"][f"/api{route.path}"][sorted(route.methods)[0].lower()]


def depends_on(dependant: Dependant, call) -> bool:
    return any(sub.call is call or depends_on(sub, call) for sub in dependant.dependencies)


def takes_checked_input(dependant: Dependant) -> bool:
    checked_path = any(param.field_info.annotation is not str for param in dependant.path_params)
    return bool(checked_path or dependant.query_params or dependant.body_params) or any(
        takes_checked_input(sub) for sub in dependant.dependencies
    )


def documented_errors(route):
    return {
        int(status): response["content"]["application/json"]["schema"]["$ref"]
        for status, response in operation(route)["responses"].items()
        if int(status) >= 400
    }


@pytest.mark.parametrize("route", API_ROUTES, ids=route_id)
def test_each_route_documents_its_errors_in_the_real_shape(route):
    errors = documented_errors(route)

    if depends_on(route.dependant, get_current_user):
        assert 401 in errors
    if takes_checked_input(route.dependant):
        assert 422 in errors
    assert set(errors.values()) <= {ERROR_SHAPE}


def test_the_framework_default_error_shape_is_gone():
    schemas = app.openapi()["components"]["schemas"]

    assert "HTTPValidationError" not in schemas
    assert "ValidationError" not in schemas


def readme_live_examples():
    section = README.read_text(encoding="utf-8").split("## Live connection", 1)[1].split("\n## ", 1)[0]
    return [json.loads(block) for block in re.findall(r"```json\n(.*?)\n```", section, re.DOTALL)]


def test_readme_live_examples_match_the_messages_the_server_sends():
    examples = readme_live_examples()
    parsed = [live_message.validate_python(example) for example in examples]

    assert {type(message) for message in parsed} == {Hello, MeetingMessage, Changed}
    assert [message.model_dump(mode="json") for message in parsed] == examples
