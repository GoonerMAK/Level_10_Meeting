import enum

from sqlalchemy import DateTime, Enum

UtcTimestamp = DateTime(timezone=True)


def pg_enum(enum_class: type[enum.Enum], name: str) -> Enum:
    return Enum(enum_class, name=name, values_callable=lambda members: [member.value for member in members])
