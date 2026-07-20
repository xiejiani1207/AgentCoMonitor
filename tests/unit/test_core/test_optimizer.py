"""Tests for ResultOptimizer."""

from agent_monitor.core.optimizer import (
    ResultOptimizer,
    RankedResult,
    OptimizationSuggestion,
    LOW_SCORE_THRESHOLD,
)
from agent_monitor.core.models import QualityDimension


def _make_result(agent_name, output, score=80, anomaly_count=0, trace_id=None):
    return {
        "trace_id": trace_id or f"t-{agent_name}",
        "agent_name": agent_name,
        "output_content": output,
        "quality_score": score,
        "anomaly_count": anomaly_count,
    }


def test_rank_sorts_by_score():
    opt = ResultOptimizer()
    results = [
        _make_result("a", "result A", score=60),
        _make_result("b", "result B", score=90),
        _make_result("c", "result C", score=75),
    ]
    ranked = opt.rank(results)
    assert ranked[0].quality_score == 90
    assert ranked[0].rank == 1
    assert ranked[0].recommendation == "adopted"


def test_rank_filters_anomalies():
    opt = ResultOptimizer()
    results = [
        _make_result("a", "result A", score=90, anomaly_count=1),
        _make_result("b", "result B", score=60, anomaly_count=0),
    ]
    ranked = opt.rank(results)
    assert len(ranked) == 1
    assert ranked[0].agent_name == "b"


def test_rank_deduplicates_by_similarity():
    opt = ResultOptimizer(similarity_threshold=0.8)
    results = [
        _make_result("a", "这只股票建议买入持有长期看好", score=90),
        _make_result("b", "这只股票建议买入持有长期看好！", score=70),  # 几乎相同
        _make_result("c", "技术面偏空建议观望等待更好的入场时机", score=80),
    ]
    ranked = opt.rank(results)
    assert len(ranked) == 2          # a 和 b 去重，保留得分高的 a
    assert ranked[0].agent_name == "a"
    assert ranked[1].agent_name == "c"


def test_top_recommendation():
    opt = ResultOptimizer()
    results = [
        _make_result("a", "result A", score=90),
        _make_result("b", "result B", score=80),
    ]
    ranked = opt.rank(results)
    top = opt.get_top_recommendation(ranked)
    assert top is not None
    assert top.recommendation == "adopted"
    assert top.quality_score == 90


def test_generate_suggestions_for_low_scores():
    opt = ResultOptimizer()
    metrics = {"compliance": 45, "accuracy": 85, "completeness": 90}
    suggestions = opt.generate_suggestions("trace-1", metrics)
    # compliance < 70 should trigger suggestions (human + agent = 2)
    compliance_suggestions = [s for s in suggestions if s.dimension == "compliance"]
    assert len(compliance_suggestions) == 2
    assert compliance_suggestions[0].target == "human"
    assert compliance_suggestions[1].target == "agent"
    assert compliance_suggestions[1].structured_cmd is not None


def test_no_suggestions_for_high_scores():
    opt = ResultOptimizer()
    metrics = {"compliance": 95, "accuracy": 90}
    suggestions = opt.generate_suggestions("trace-1", metrics)
    assert len(suggestions) == 0


def test_empty_results():
    opt = ResultOptimizer()
    ranked = opt.rank([])
    assert len(ranked) == 0
    assert opt.get_top_recommendation(ranked) is None
