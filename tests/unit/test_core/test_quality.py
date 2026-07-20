"""Tests for QualityAssessor."""

from agent_monitor.core.quality import QualityAssessor
from agent_monitor.core.models import TraceRecord, TraceStatus


def _make_trace(**overrides) -> TraceRecord:
    defaults = dict(
        agent_name="test_agent",
        agent_role="tester",
        task_id="task-1",
        input_prompt="分析股票 600519 的投资价值",
        output_content="根据技术面和基本面分析，建议买入该股票。请注意风险。",
        status=TraceStatus.SUCCESS,
    )
    return TraceRecord(**{**defaults, **overrides})


def test_clean_output_scores_high():
    assessor = QualityAssessor()
    trace = _make_trace(output_content="综合分析后，建议投资者关注该标的，注意仓位控制和风险防范。根据近期走势分析，该股票在支撑位附近有较强买盘。")
    result = assessor.evaluate(trace)
    assert result.compliance == 100.0  # no banned words
    assert result.overall_score > 0
    assert result.eval_method in ("rule", "rule_only")


def test_compliance_violation_detected():
    assessor = QualityAssessor()
    trace = _make_trace(output_content="这只股票包赚不亏，保证收益，稳赚！")
    result = assessor.evaluate(trace)
    assert result.compliance is not None
    assert result.compliance < 60  # multiple violations


def test_compliance_blocks_llm_layer():
    assessor = QualityAssessor()
    trace = _make_trace(output_content="保证收益 稳赚 无风险 绝对 必然")  # 5 violations → score 0
    result = assessor.evaluate(trace)
    assert result.eval_method == "rule_only"
    assert result.compliance == 0.0


def test_empty_output_scores_zero():
    assessor = QualityAssessor()
    trace = _make_trace(output_content="")
    result = assessor.evaluate(trace)
    assert result.completeness is not None
    assert result.completeness < 100


def test_overall_score_with_custom_weights():
    assessor = QualityAssessor(weights={"compliance": 1.0})  # only compliance matters
    trace = _make_trace(output_content="this is fine")
    result = assessor.evaluate(trace)
    assert result.overall_score == 100.0  # compliance is clean
