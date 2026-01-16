"""Add audit_log table for compliance traceability.

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-16

Creates the audit_logs table for:
- Tracking extraction events (started, completed, failed)
- Tracking validation events (rule applied, finding generated)
- AI model traceability (model_version, prompt_version)
- Compliance auditing (AUDT-01 to AUDT-05)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create audit_logs table."""
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "event_type",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "event_timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "details",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "model_version",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "prompt_version",
            sa.String(50),
            nullable=True,
        ),
        sa.Column(
            "confidence_score",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "rule_id",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
        sa.ForeignKeyConstraint(
            ["analysis_id"],
            ["analyses.id"],
            name="fk_audit_logs_analysis_id_analyses",
            ondelete="CASCADE",
        ),
    )
    # Composite index for efficient queries by analysis and time
    op.create_index(
        "ix_audit_logs_analysis_id_event_timestamp",
        "audit_logs",
        ["analysis_id", "event_timestamp"],
    )


def downgrade() -> None:
    """Drop audit_logs table."""
    op.drop_index(
        "ix_audit_logs_analysis_id_event_timestamp",
        table_name="audit_logs",
    )
    op.drop_table("audit_logs")
