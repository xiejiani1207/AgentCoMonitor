"""Demo：完整监控链路演示脚本。

模拟一次 5 Agent 投顾任务，展示每个模块的输出。
运行: python demo_pipeline.py
"""

from datetime import datetime

from agent_monitor.core.models import TraceRecord, TraceStatus
from agent_monitor.core.anomaly import AnomalyDetector
from agent_monitor.core.quality import QualityAssessor
from agent_monitor.core.optimizer import ResultOptimizer


def build_traces() -> list[TraceRecord]:
    """构建 5 条模拟 Trace：数据采集 → 并行分析 → 风控 → 决策。"""
    now = datetime(2026, 7, 20, 10, 0, 0)
    task_id = "task-demo-001"
    traces = []

    t0 = TraceRecord(
        trace_id="t-collector-1", task_id=task_id,
        agent_name="data_collector", agent_role="数据采集员",
        input_prompt="用户查询：分析 600519 贵州茅台",
        output_content="已采集行情：当前价 1680.50，PE 28.5，PB 9.2，ROE 32.1%，营收增长 18%。",
        start_time=now, end_time=datetime(2026, 7, 20, 10, 0, 2),
        duration_ms=2000, token_used=150, status=TraceStatus.SUCCESS,
    )
    traces.append(t0)

    t1 = TraceRecord(
        trace_id="t-technical-1", task_id=task_id,
        agent_name="technical_analyst", agent_role="技术面分析师",
        parent_trace_id=t0.trace_id, input_prompt=t0.output_content,
        output_content=(
            "技术面分析：MA5 上穿 MA20 形成金叉，MACD 红柱放大，"
            "RSI 58 处于健康区间。支撑位 1600，压力位 1750。短期趋势偏多。"
        ),
        start_time=datetime(2026, 7, 20, 10, 0, 2),
        end_time=datetime(2026, 7, 20, 10, 0, 7),
        duration_ms=5000, token_used=300, status=TraceStatus.SUCCESS,
    )
    traces.append(t1)

    t2 = TraceRecord(
        trace_id="t-fundamental-1", task_id=task_id,
        agent_name="fundamental_analyst", agent_role="基本面分析师",
        parent_trace_id=t0.trace_id, input_prompt=t0.output_content,
        output_content=(
            "基本面分析：PE 28.5 低于行业均值 32.0，PB 9.2 高于行业均值 8.5。"
            "ROE 32.1% 行业领先。营收增长 18%，利润增长 15%。估值合理，成长性良好。"
        ),
        start_time=datetime(2026, 7, 20, 10, 0, 2),
        end_time=datetime(2026, 7, 20, 10, 0, 6),
        duration_ms=4000, token_used=280, status=TraceStatus.SUCCESS,
    )
    traces.append(t2)

    t3 = TraceRecord(
        trace_id="t-risk-1", task_id=task_id,
        agent_name="risk_assessor", agent_role="风控评估员",
        parent_trace_id=t1.trace_id,
        input_prompt=f"{t1.output_content}\n\n{t2.output_content}",
        output_content=(
            "风控评估：技术面和基本面均偏多，综合考虑建议仓位 20% 以内。"
            "止损位 1550。综合风险等级：中等。"
        ),
        start_time=datetime(2026, 7, 20, 10, 0, 7),
        end_time=datetime(2026, 7, 20, 10, 0, 10),
        duration_ms=3000, token_used=200, status=TraceStatus.SUCCESS,
    )
    traces.append(t3)

    t4 = TraceRecord(
        trace_id="t-decision-1", task_id=task_id,
        agent_name="decision_maker", agent_role="综合决策官",
        parent_trace_id=t3.trace_id, input_prompt=t3.output_content,
        output_content=(
            "综合投资建议：贵州茅台（600519）技术偏多，基本面稳健，风险可控。"
            "建议逢低买入，目标价 1750，止损 1550。注意仓位管理，切勿追高。"
            "保证收益。稳赚不赔。"  # ← 故意放的合规问题
        ),
        start_time=datetime(2026, 7, 20, 10, 0, 10),
        end_time=datetime(2026, 7, 20, 10, 0, 13),
        duration_ms=3000, token_used=350, status=TraceStatus.SUCCESS,
    )
    traces.append(t4)

    return traces


async def demo_async():
    traces = build_traces()

    anomaly_detector = AnomalyDetector(timeout_ms=30000)
    quality_assessor = QualityAssessor()
    result_optimizer = ResultOptimizer()

    sep = "=" * 70

    # ==================== 逐个 Agent 展示 ====================
    results_for_ranking = []

    for i, trace in enumerate(traces, 1):
        print(f"\n{sep}")
        print(f"  Agent {i}: {trace.agent_name} ({trace.agent_role})")
        print(f"{sep}")

        # ---- 异常检测 ----
        anomalies = anomaly_detector.detect(trace)
        if anomalies:
            print(f"  [异常检测] 发现 {len(anomalies)} 个异常:")
            for a in anomalies:
                print(f"    [{a.severity.upper()}] {a.anomaly_type}")
                print(f"            {a.description}")
        else:
            print("  [异常检测] 无异常")

        # ---- 质量评估 ----
        quality = await quality_assessor.evaluate_async(trace)
        print(f"  [质量评估] 综合分: {quality.overall_score}  (方法: {quality.eval_method})")
        print(f"    合规性: {quality.compliance:>6.1f}  |  准确性: {quality.accuracy:>6.1f}")
        print(f"    完整性: {quality.completeness:>6.1f}  |  相关性: {quality.relevance:>6.1f}")
        print(f"    时效性: {quality.timeliness:>6.1f}")

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

    # ==================== 筛选排名 ====================
    print(f"\n\n{sep}")
    print("  筛选优化结果")
    print(f"{sep}")

    ranked = result_optimizer.rank(results_for_ranking)

    for r in ranked:
        badge = {"adopted": "采纳", "alternative": "备选", "archived": "存档"}[r.recommendation]
        print(f"  #{r.rank} [{badge}] {r.agent_name:25s}  得分: {r.quality_score:>6.1f}")

    # ==================== 优化建议 ====================
    print(f"\n{sep}")
    print("  优化建议（针对低分维度）")
    print(f"{sep}")

    for r in results_for_ranking:
        metrics = {k: v for k, v in r["quality_metrics"].items() if v is not None}
        suggestions = result_optimizer.generate_suggestions(r["trace_id"], metrics)
        if suggestions:
            print(f"\n  Agent: {r['agent_name']}")
            for s in suggestions:
                icon = "[人]" if s.target == "human" else "[机]"
                print(f"    {icon} [{s.dimension}] {s.content}")

    print(f"\n{sep}")
    print(f"  Demo 完成 — {len(traces)} 条 Trace → 异常检测 → 质量评估 → 筛选优化")
    print(f"{sep}\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_async())
