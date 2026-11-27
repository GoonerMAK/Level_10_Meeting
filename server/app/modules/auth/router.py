from fastapi import APIRouter, Request, status

from app.db.session import DbSession
from app.modules.auth import service
from app.modules.auth.dependencies import SignedInUser
from app.modules.auth.schemas import Me, SignIn, UserChoice

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/users")
async def read_users(session: DbSession) -> list[UserChoice]:
    return await service.list_users(session)


@router.post("/sign-in")
async def sign_in(body: SignIn, request: Request, session: DbSession) -> Me:
    return Me.from_user(await service.sign_in(session, request.session, body.user_id))


@router.post("/sign-out", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(request: Request) -> None:
    request.session.clear()


@router.get("/me")
async def read_me(current_user: SignedInUser) -> Me:
    return Me.from_user(current_user)
