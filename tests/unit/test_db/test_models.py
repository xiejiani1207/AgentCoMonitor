"""Tests for SQLAlchemy ORM model definitions (no DB connection required)."""

from agent_monitor.db import models  # noqa: F401 — ensure tables registered
from agent_monitor.db.models import Trace
from agent_monitor.db.session import Base


def test_tables_defined():
    """All five core tables are defined in metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected = {"tasks", "traces", "anomaly_events", "quality_scores", "optimization_suggestions"}
    assert table_names >= expected


def test_trace_columns():
    """Trace model has expected columns."""
    cols = {c.name for c in Trace.__table__.columns}
    assert "trace_id" in cols
    assert "task_id" in cols
    assert "agent_name" in cols
    assert "parent_trace_id" in cols
    assert "status" in cols
    assert "quality_score" in cols
    assert "quality_metrics" in cols
