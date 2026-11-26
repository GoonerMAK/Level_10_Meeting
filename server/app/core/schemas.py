from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer, StringConstraints

JsonNumber = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Note = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class UserRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
