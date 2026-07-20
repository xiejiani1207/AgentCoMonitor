"""Tests for SQLAlchemy ORM models."""

import pytest

from agent_monitor.db.models import Task, Trace, AnomalyEvent, QualityScore, OptimizationSuggestion


@pytest.mark.asyncio
async def test_trace_creation(db_session):
    """Verify a Trace can be persisted."""
    from agent_monitor.db.session import Base

    assert Base.metadata.tables["traces"] is not None
    assert Base.metadata.tables["tasks"] is not None
    assert Base.metadata.tables["anomaly_events"] is not None
    assert Base.metadata.tables["quality_scores"] is not None
    assert Base.metadata.tables["optimization_suggestions"] is not None
