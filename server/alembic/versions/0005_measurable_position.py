"""keep Measurables in the seed's order

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-27 22:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0005'
down_revision: str | None = '0004'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('measurables', sa.Column('position', sa.SmallInteger(), nullable=True))
    op.execute(
        'UPDATE measurables SET position = ordered.position FROM ('
        'SELECT id, row_number() OVER (PARTITION BY team_id ORDER BY id) AS position FROM measurables'
        ') AS ordered WHERE measurables.id = ordered.id'
    )
    op.alter_column('measurables', 'position', nullable=False)


def downgrade() -> None:
    op.drop_column('measurables', 'position')
