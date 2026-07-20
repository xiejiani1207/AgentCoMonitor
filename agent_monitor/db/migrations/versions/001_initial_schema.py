"""Initial schema — traces, anomaly_events, quality_scores, optimization_suggestions, tasks

Revision ID: 001
Revises: None
Create Date: 2026-07-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(256), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="task_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )

    op.create_table(
        "traces",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("trace_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("agent_name", sa.String(128), nullable=False),
        sa.Column("agent_role", sa.String(256), nullable=True),
        sa.Column("parent_trace_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("input_prompt", sa.Text(), nullable=True),
        sa.Column("output_content", sa.Text(), nullable=True),
        sa.Column("token_used", sa.Integer(), nullable=True),
        sa.Column("decision_type", sa.String(64), nullable=True),
        sa.Column("decision_summary", sa.Text(), nullable=True),
        sa.Column("tool_calls", postgresql.JSONB(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "success", "error", "retry", "timeout", name="trace_status"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("quality_metrics", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.task_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trace_id"),
    )
    op.create_index("idx_traces_task_time", "traces", ["task_id", "start_time"])
    op.create_index("idx_traces_agent_status", "traces", ["agent_name", "status"])
    op.create_index("idx_traces_parent", "traces", ["parent_trace_id"])

    op.create_table(
        "anomaly_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("trace_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("anomaly_type", sa.String(64), nullable=False),
        sa.Column(
            "severity",
            sa.Enum("high", "medium", "low", name="anomaly_severity"),
            nullable=False,
        ),
        sa.Column(
            "layer",
            sa.Enum("execution", "behavior", "output", name="anomaly_layer"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["trace_id"], ["traces.trace_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_anomalies_severity_time", "anomaly_events", ["severity", "created_at"])
    op.create_index("idx_anomalies_task", "anomaly_events", ["task_id"])

    op.create_table(
        "quality_scores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("trace_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("completeness", sa.Float(), nullable=True),
        sa.Column("relevance", sa.Float(), nullable=True),
        sa.Column("compliance", sa.Float(), nullable=True),
        sa.Column("timeliness", sa.Float(), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("eval_method", sa.String(32), nullable=True),
        sa.Column("eval_detail", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["trace_id"], ["traces.trace_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("trace_id"),
    )
    op.create_index("idx_quality_trace", "quality_scores", ["trace_id"])
    op.create_index("idx_quality_score", "quality_scores", ["overall_score"])

    op.create_table(
        "optimization_suggestions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("trace_id", postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column(
            "target",
            sa.Enum("human", "agent", name="suggestion_target"),
            nullable=False,
        ),
        sa.Column("low_dimension", sa.String(32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_cmd", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["trace_id"], ["traces.trace_id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("optimization_suggestions")
    op.drop_table("quality_scores")
    op.drop_table("anomaly_events")
    op.drop_table("traces")
    op.drop_table("tasks")
    # Drop enums
    op.execute("DROP TYPE IF EXISTS suggestion_target")
    op.execute("DROP TYPE IF EXISTS anomaly_layer")
    op.execute("DROP TYPE IF EXISTS anomaly_severity")
    op.execute("DROP TYPE IF EXISTS trace_status")
    op.execute("DROP TYPE IF EXISTS task_status")
