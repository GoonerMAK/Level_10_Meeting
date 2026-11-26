from pydantic import BaseModel

from app.models.enums import UserRole


class Me(BaseModel):
    id: str
    name: str
    email: str
    role: UserRole
    team_ids: list[str]
