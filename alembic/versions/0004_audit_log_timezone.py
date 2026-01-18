"""Fix audit_logs event_timestamp to use timezone.

Revision ID: 0004
Revises: 0003
Create Date: 2026-01-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter event_timestamp from TIMESTAMP WITHOUT TIME ZONE to TIMESTAMP WITH TIME ZONE
    op.alter_column(
        'audit_logs',
        'event_timestamp',
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False),
        existing_nullable=False,
        existing_server_default=sa.text('now()'),
    )


def downgrade() -> None:
    op.alter_column(
        'audit_logs',
        'event_timestamp',
        type_=sa.DateTime(timezone=False),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text('now()'),
    )
