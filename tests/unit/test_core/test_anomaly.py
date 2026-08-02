"""Tests for AnomalyDetector."""

from agent_monitor.core.anomaly import AnomalyDetector
from agent_monitor.core.models import AnomalySeverity, TraceRecord, TraceStatus


def _make_trace(**overrides) -> TraceRecord:
    defaults = {
        "agent_name": "test_agent",
        "agent_role": "tester",
        "task_id": "task-1",
        "input_prompt": "hello",
        "output_content": "world output is long enough",
        "status": TraceStatus.SUCCESS,
    }
    return TraceRecord(**{**defaults, **overrides})


def test_successful_trace_no_anomalies():
    detector = AnomalyDetector()
    trace = _make_trace()
    results = detector.detect(trace)
    assert len(results) == 0


def test_error_trace_detected():
    detector = AnomalyDetector()
    trace = _make_trace(status=TraceStatus.ERROR, error_message="boom")
    results = detector.detect(trace)
    assert any(r.anomaly_type == "execution_error" for r in results)
    assert any(r.severity == AnomalySeverity.HIGH for r in results)


def test_timeout_detected():
    detector = AnomalyDetector(timeout_ms=5000)
    trace = _make_trace(duration_ms=6000)
    results = detector.detect(trace)
    assert any(r.anomaly_type == "timeout" for r in results)


def test_empty_output_detected():
    detector = AnomalyDetector()
    trace = _make_trace(output_content="   ")
    results = detector.detect(trace)
    assert any(r.anomaly_type == "empty_output" for r in results)


def test_loop_detected():
    detector = AnomalyDetector()
    trace1 = _make_trace()
    trace2 = _make_trace()  # same agent + same input

    results1 = detector.detect(trace1)
    assert not any(r.anomaly_type == "loop_detected" for r in results1)

    results2 = detector.detect(trace2)
    assert any(r.anomaly_type == "loop_detected" for r in results2)


def test_invalid_tool_call_detected():
    detector = AnomalyDetector()
    trace = _make_trace(tool_calls=[{"args": "test"}])  # no tool_name
    results = detector.detect(trace)
    assert any(r.anomaly_type == "invalid_tool_call" for r in results)


def test_check_required_agents():
    detector = AnomalyDetector()
    results = detector.check_required_agents(
        completed_agents={"collector", "analyst"},
        required_agents={"collector", "analyst", "risk"},
        task_id="task-1",
    )
    assert len(results) == 1
    assert results[0].anomaly_type == "missing_required_agent"
    assert "risk" in results[0].description
