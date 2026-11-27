from typing import Annotated

from fastapi import APIRouter, Query

from app.core.error_docs import error_responses
from app.db.session import DbSession
from app.modules.activity import service
from app.modules.activity.schemas import ActivityOut
from app.modules.auth.dependencies import SignedInUser

router = APIRouter(tags=["activity"])


@router.get("/teams/{team_id}/activity", responses=error_responses(401, 404, 422))
async def read_activity(
    team_id: str,
    session: DbSession,
    current_user: SignedInUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    before_id: Annotated[int | None, Query(ge=1)] = None,
) -> list[ActivityOut]:
    return await service.list_activity(session, current_user, team_id, limit, before_id)
