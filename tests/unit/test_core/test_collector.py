"""Tests for TraceCollector."""

from datetime import datetime

from agent_monitor.core.collector import TraceCollector
from agent_monitor.core.models import TraceRecord, TraceStatus


def test_collector_init():
    """Collector can be instantiated with or without ws_notifier."""
    c1 = TraceCollector()
    assert c1._ws_notifier is None

    async def noop(_): pass
    c2 = TraceCollector(ws_notifier=noop)
    assert c2._ws_notifier is not None


def test_trace_to_orm_mapping():
    """TraceRecord fields map correctly (smoke check without DB)."""
    trace = TraceRecord(
        trace_id="abc-123",
        task_id="task-1",
        agent_name="test_agent",
        agent_role="tester",
        parent_trace_id="parent-456",
        start_time=datetime(2026, 7, 20, 10, 0, 0),
        end_time=datetime(2026, 7, 20, 10, 0, 5),
        duration_ms=5000,
        input_prompt="hello",
        output_content="world",
        token_used=42,
        decision_type="analysis",
        decision_summary="looks good",
        tool_calls=[{"tool": "echo"}],
        status=TraceStatus.SUCCESS,
    )
    assert trace.trace_id == "abc-123"
    assert trace.status == "success"
    assert trace.duration_ms == 5000
    assert trace.token_used == 42
    assert len(trace.tool_calls) == 1
