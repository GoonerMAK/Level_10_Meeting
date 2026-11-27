from fastapi import APIRouter

from app.core.error_docs import error_responses
from app.db.session import DbSession
from app.modules.auth.dependencies import SignedInUser
from app.modules.rocks import service
from app.modules.rocks.schemas import RockList

router = APIRouter(tags=["rocks"])


@router.get("/teams/{team_id}/rocks", responses=error_responses(401, 404))
async def read_rocks(team_id: str, session: DbSession, current_user: SignedInUser) -> RockList:
    return await service.list_rocks(session, current_user, team_id)
