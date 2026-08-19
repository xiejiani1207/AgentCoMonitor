"""add agent_instructions table

Revision ID: 002
Revises: 001
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_instructions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("target_agent", sa.String(128), nullable=False),
        sa.Column("dimension", sa.String(32), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_instructions_agent_status", "agent_instructions", ["target_agent", "status"]
    )


def downgrade() -> None:
    op.drop_index("idx_instructions_agent_status", table_name="agent_instructions")
    op.drop_table("agent_instructions")
