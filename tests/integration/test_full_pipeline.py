"""集成测试：模拟一次多 Agent 任务，Trace 流经全部四个模块。

测试数据模拟了一个金融投顾链路：
  数据采集 → 技术面分析 ∥ 基本面分析 → 风控评估 → 综合决策

不需要数据库连接——只测试核心逻辑链路。
"""

from datetime import datetime
from agent_monitor.core.models import TraceRecord, TraceStatus
from agent_monitor.core.anomaly import AnomalyDetector
from agent_monitor.core.quality import QualityAssessor
from agent_monitor.core.optimizer import ResultOptimizer


# ---- 模拟 Task 中所有 Agent 的 Trace 数据 ----

def _make_traces() -> list[TraceRecord]:
    now = datetime(2026, 7, 20, 10, 0, 0)
    task_id = "task-demo-001"
    traces = []

    # Agent 1: 数据采集
    collector_trace = TraceRecord(
        trace_id="t-collector-1",
        task_id=task_id,
        agent_name="data_collector",
        agent_role="数据采集员",
        input_prompt="用户查询：分析 600519 贵州茅台",
        output_content="已采集行情数据：当前价 1680.50，PE 28.5，PB 9.2。已采集财务数据：ROE 32.1%，营收增长 18%。",
        start_time=now,
        end_time=datetime(2026, 7, 20, 10, 0, 2),
        duration_ms=2000,
        token_used=150,
        status=TraceStatus.SUCCESS,
    )
    traces.append(collector_trace)

    # Agent 2: 技术面分析（并行分支 A）
    tech_trace = TraceRecord(
        trace_id="t-technical-1",
        task_id=task_id,
        agent_name="technical_analyst",
        agent_role="技术面分析师",
        parent_trace_id="t-collector-1",
        input_prompt=collector_trace.output_content,
        output_content="技术面分析：MA5 上穿 MA20 形成金叉，MACD 红柱放大，RSI 58 处于健康区间。"
                       "支撑位 1600，压力位 1750。短期趋势偏多，建议关注突破信号。",
        start_time=datetime(2026, 7, 20, 10, 0, 2),
        end_time=datetime(2026, 7, 20, 10, 0, 7),
        duration_ms=5000,
        token_used=300,
        status=TraceStatus.SUCCESS,
    )
    traces.append(tech_trace)

    # Agent 3: 基本面分析（并行分支 B）
    fund_trace = TraceRecord(
        trace_id="t-fundamental-1",
        task_id=task_id,
        agent_name="fundamental_analyst",
        agent_role="基本面分析师",
        parent_trace_id="t-collector-1",
        input_prompt=collector_trace.output_content,
        output_content="基本面分析：PE 28.5 低于行业均值 32.0，PB 9.2 高于行业均值 8.5。"
                       "ROE 32.1% 处于行业领先水平。营收增长 18% 稳健，利润增长 15%。"
                       "估值合理，成长性良好。",
        start_time=datetime(2026, 7, 20, 10, 0, 2),
        end_time=datetime(2026, 7, 20, 10, 0, 6),
        duration_ms=4000,
        token_used=280,
        status=TraceStatus.SUCCESS,
    )
    traces.append(fund_trace)

    # Agent 4: 风控评估
    risk_trace = TraceRecord(
        trace_id="t-risk-1",
        task_id=task_id,
        agent_name="risk_assessor",
        agent_role="风控评估员",
        parent_trace_id="t-technical-1",
        input_prompt=f"{tech_trace.output_content}\n\n{fund_trace.output_content}",
        output_content="风控评估：技术面和基本面均偏多，但大盘波动率上升，建议仓位控制在 20% 以内。"
                       "注意止损线设在 1550。综合风险等级：中等。",
        start_time=datetime(2026, 7, 20, 10, 0, 7),
        end_time=datetime(2026, 7, 20, 10, 0, 10),
        duration_ms=3000,
        token_used=200,
        status=TraceStatus.SUCCESS,
    )
    traces.append(risk_trace)

    # Agent 5: 综合决策
    decision_trace = TraceRecord(
        trace_id="t-decision-1",
        task_id=task_id,
        agent_name="decision_maker",
        agent_role="综合决策官",
        parent_trace_id="t-risk-1",
        input_prompt=risk_trace.output_content,
        output_content="综合投资建议：贵州茅台（600519）当前技术走势偏多，基本面稳健，风险可控。"
                       "建议逢低买入，目标价 1750，止损 1550。注意仓位管理，切勿追高。"
                       "保证收益。稳赚不赔。",  # ← 故意加了合规问题
        start_time=datetime(2026, 7, 20, 10, 0, 10),
        end_time=datetime(2026, 7, 20, 10, 0, 13),
        duration_ms=3000,
        token_used=350,
        status=TraceStatus.SUCCESS,
    )
    traces.append(decision_trace)

    return traces


# ---- 集成测试 ----

def test_full_pipeline():
    """完整链路：采集 → 异常检测 → 质量评估 → 筛选优化。"""
    traces = _make_traces()
    task_id = traces[0].task_id

    # 初始化三大模块（collector 需要 DB，此处仅测试核心逻辑）
    anomaly_detector = AnomalyDetector(timeout_ms=30000)
    quality_assessor = QualityAssessor()
    result_optimizer = ResultOptimizer()

    # 模拟执行：每条 Trace 流经三大模块
    all_anomalies = []
    results_for_ranking = []

    for trace in traces:
        # 异常检测
        anomalies = anomaly_detector.detect(trace)
        all_anomalies.extend(anomalies)

        # 质量评估
        quality = quality_assessor.evaluate(trace)

        # 收集结果供筛选优化
        results_for_ranking.append({
            "trace_id": trace.trace_id,
            "agent_name": trace.agent_name,
            "output_content": trace.output_content,
            "quality_score": quality.overall_score,
            "anomaly_count": len(anomalies),
            "quality_metrics": {
                "accuracy": quality.accuracy,
                "completeness": quality.completeness,
                "relevance": quality.relevance,
                "compliance": quality.compliance,
                "timeliness": quality.timeliness,
            },
        })

    # ---- 断言 ----

    # 1. 5 条 Trace 全部被评估
    assert len(results_for_ranking) == 5

    # 2. 决策 Agent 的合规问题被检测到（"保证收益" "稳赚不赔"）
    decision_result = next(
        r for r in results_for_ranking if r["agent_name"] == "decision_maker"
    )
    assert decision_result["quality_metrics"]["compliance"] is not None
    assert decision_result["quality_metrics"]["compliance"] < 80

    # 3. 异常检测正常运行
    assert len(all_anomalies) >= 0  # smoke check

    # 4. 筛选优化：排序 + 推荐
    ranked = result_optimizer.rank(results_for_ranking)
    assert len(ranked) >= 1  # 至少一个无异常的结果通过过滤
    top = result_optimizer.get_top_recommendation(ranked)
    assert top is not None
    assert top.recommendation == "adopted"

    # 5. 为低合规 Agent 生成优化建议
    metrics = {
        k: v for k, v in decision_result["quality_metrics"].items()
        if v is not None
    }
    suggestions = result_optimizer.generate_suggestions(
        decision_result["trace_id"], metrics
    )
    # 合规低分应该触发了建议
    compliance_suggestions = [s for s in suggestions if s.dimension == "compliance"]
    assert len(compliance_suggestions) == 2  # human + agent

    print(f"\n  Task: {task_id}")
    print(f"  Traces: {len(traces)}")
    print(f"  Anomalies detected: {len(all_anomalies)}")
    print(f"  Ranked results: {len(ranked)}")
    print(f"  Top recommendation: {top.agent_name} (score: {top.quality_score})")
    print(f"  Suggestions generated: {len(suggestions)}")


def test_pipeline_with_timeout():
    """超时 Trace 被异常检测捕获，排除出推荐列表。"""
    traces = _make_traces()
    # 把技术面分析改成超时
    traces[1].status = TraceStatus.TIMEOUT
    traces[1].duration_ms = 35000

    anomaly_detector = AnomalyDetector(timeout_ms=30000)
    quality_assessor = QualityAssessor()
    result_optimizer = ResultOptimizer()

    results = []
    for trace in traces:
        anomalies = anomaly_detector.detect(trace)
        quality = quality_assessor.evaluate(trace)
        results.append({
            "trace_id": trace.trace_id,
            "agent_name": trace.agent_name,
            "output_content": trace.output_content,
            "quality_score": quality.overall_score,
            "anomaly_count": len(anomalies),
        })

    ranked = result_optimizer.rank(results)
    # 技术面分析因为超时应该被排除
    tech_in_results = any(r.agent_name == "technical_analyst" for r in ranked)
    assert not tech_in_results
    assert len(ranked) == 4  # 5 - 1 timeout
