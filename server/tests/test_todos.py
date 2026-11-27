import pytest
from sqlalchemy import delete

from app.db.session import SessionLocal, engine
from app.models import Todo

ADD_TODO_URL = "/api/issues/i8/todos"


@pytest.mark.anyio
async def test_an_admin_off_the_team_can_own_a_todo(signed_in_clients):
    async with signed_in_clients("u6") as clients:
        response = await clients["u6"].post(ADD_TODO_URL, json={"title": "Call the ad agency", "owner_id": "u1"})
    try:
        assert response.status_code == 201
        assert response.json()["owner"] == {"id": "u1", "name": "Avery Admin"}
    finally:
        await delete_todo(response.json().get("id"))
        await engine.dispose()


@pytest.mark.anyio
@pytest.mark.parametrize("owner_id", ["u7", "u8", "nobody"], ids=["observer", "other_team_member", "unknown_user"])
async def test_owner_must_be_a_team_member_or_an_admin(signed_in_clients, owner_id):
    async with signed_in_clients("u6") as clients:
        response = await clients["u6"].post(ADD_TODO_URL, json={"title": "Call the ad agency", "owner_id": owner_id})
    await engine.dispose()

    assert response.status_code == 422
    assert response.json()["error"]["fields"] == [
        {"field": "owner_id", "message": "Owner must be a Team Member of this team or an Admin"}
    ]


async def delete_todo(todo_id):
    if todo_id is None:
        return
    async with SessionLocal() as session:
        await session.execute(delete(Todo).where(Todo.id == todo_id))
        await session.commit()
