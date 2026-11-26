from fastapi import APIRouter

from app.modules.auth.dependencies import SignedInUser
from app.modules.auth.schemas import Me

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def read_me(current_user: SignedInUser) -> Me:
    return Me(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        team_ids=sorted(current_user.team_ids),
    )
