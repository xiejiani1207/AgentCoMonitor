"""端到端演示：投顾 Demo → 监控采集 → 异常/质量/筛选 → 落库。

运行一次真实投顾任务，通过 LangGraph 适配器零侵入采集 Trace，
再经 MonitoringPipeline 串联四模块写入 PostgreSQL。

运行:
  python run_monitored_demo.py                     # 正常链路
  python run_monitored_demo.py --inject-violation  # 注入合规违规 + 超时异常
"""

import argparse
import asyncio

from agent_monitor.adapters.langgraph import LangGraphCallback
from agent_monitor.core.pipeline import MonitoringPipeline
from demo_advisory.graph import build_graph


def inject_issues(collected: list) -> None:
    """注入演示问题，用于展示检测能力：
    - 决策 Agent 追加合规违规话术（触发合规检测 + 优化建议）
    - 技术面 Agent 改成超时（触发超时异常，进入异常告警）
    """
    for trace in collected:
        if trace.agent_name == "decision_maker":
            trace.output_content += "\n\n【注入】保证收益。稳赚不赔。"
        elif trace.agent_name == "technical_analyst":
            trace.duration_ms = 35000  # 超过默认 30s 超时阈值


async def main(inject: bool = False) -> None:
    query = "分析 600519 贵州茅台"
    pipeline = MonitoringPipeline()

    collected: list = []
    monitor = LangGraphCallback(on_trace=collected.append)

    sep = "=" * 70
    print(f"查询: {query}")
    print(sep)

    graph = build_graph()
    await monitor.run(graph, {"query": query})

    if inject:
        inject_issues(collected)
        print("  [注入] 决策 Agent 合规违规 + 技术面超时已注入")

    print(f"采集到 {len(collected)} 条 Trace")

    processed = []
    for i, trace in enumerate(collected, 1):
        print(f"  处理 Trace {i}/{len(collected)}: {trace.agent_name}")
        processed.append(await pipeline.process_trace(trace))

    if collected:
        await pipeline.finalize_task(collected[0].task_id)

    ranked = pipeline.rank(processed)

    # ---- 汇总输出 ----
    print(f"\n{sep}")
    print("  监控管线结果")
    print(sep)

    for r in processed:
        trace = r["trace"]
        quality = r["quality"]
        print(f"\n  Agent: {trace.agent_name}")
        print(f"    状态: {trace.status} | 耗时: {trace.duration_ms}ms | token: {trace.token_used}")
        if r["anomalies"]:
            for a in r["anomalies"]:
                print(f"    [异常/{a.severity}] {a.anomaly_type}: {a.description}")
        else:
            print("    [异常] 无")
        print(f"    [质量] 综合分 {quality.overall_score} ({quality.eval_method}) 合规 {quality.compliance}")
        for s in r["suggestions"]:
            icon = "[人]" if s.target == "human" else "[机]"
            print(f"    [建议{icon}] {s.dimension}: {s.content}")

    print(f"\n{sep}")
    print("  筛选排序")
    print(sep)
    for r in ranked:
        badge = {"adopted": "采纳", "alternative": "备选", "archived": "存档"}[r.recommendation]
        print(f"  #{r.rank} [{badge}] {r.agent_name:20s} 得分: {r.quality_score:>6.1f}")

    print("\n完成 - 数据已写入 PostgreSQL，可在 Dashboard 查看")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="端到端监控演示")
    parser.add_argument(
        "--inject-violation", action="store_true", help="注入合规违规 + 超时异常"
    )
    args = parser.parse_args()
    asyncio.run(main(inject=args.inject_violation))
