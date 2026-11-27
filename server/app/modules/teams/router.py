from fastapi import APIRouter

from app.db.session import DbSession
from app.modules.auth.dependencies import SignedInUser
from app.modules.teams import service
from app.modules.teams.schemas import TeamDetail, TeamMember, TeamSummary, TodoOwner

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("")
async def read_teams(session: DbSession, current_user: SignedInUser) -> list[TeamSummary]:
    teams = await service.list_teams(session, current_user)
    return [TeamSummary.model_validate(team) for team in teams]


@router.get("/{team_id}")
async def read_team(team_id: str, session: DbSession, current_user: SignedInUser) -> TeamDetail:
    team, members = await service.get_team_with_members(session, current_user, team_id)
    owners = await service.list_todo_owners(session, team_id)
    return TeamDetail(
        id=team.id,
        name=team.name,
        members=[TeamMember.model_validate(member) for member in members],
        todo_owners=[
            TodoOwner(id=owner.id, name=owner.name, role=owner.role, on_team=on_team) for owner, on_team in owners
        ],
    )
