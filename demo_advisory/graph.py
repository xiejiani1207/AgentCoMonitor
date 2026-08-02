"""LangGraph 金融投顾 Agent 链路编排。

拓扑:
  数据采集 → 技术面分析 ∥ 基本面分析 → 风控评估 → 综合决策 → 合规判断 → 最终输出

用法:
  python demo_advisory/graph.py
  或
  from demo_advisory.graph import run_advisory
  state = await run_advisory("分析 600519")
"""

from typing import TypedDict

from langgraph.graph import END, StateGraph

from demo_advisory.agents import (
    compliance_checker,
    data_collector,
    decision_maker,
    fundamental_analyst,
    risk_assessor,
    technical_analyst,
)

# ---- State 定义 ----

class AdvisoryState(TypedDict, total=False):
    query: str                          # 用户查询
    stock_code: str | None           # 股票代码
    stock_name: str | None           # 股票名称
    collected_data: dict | None      # 数据采集结果
    technical_report: str               # 技术面分析报告
    fundamental_report: str             # 基本面分析报告
    risk_report: str                    # 风控评估报告
    decision: str                       # 综合决策
    compliance_result: str              # 合规审查结果
    compliance_score: int               # 合规评分
    final_output: str                   # 最终输出（合规过滤后）
    error: str | None                # 错误信息


# ---- 构建 Graph ----

def build_graph() -> StateGraph:
    graph = StateGraph(AdvisoryState)

    # 注册所有节点
    graph.add_node("data_collector", data_collector.run)
    graph.add_node("technical_analyst", technical_analyst.run)
    graph.add_node("fundamental_analyst", fundamental_analyst.run)
    graph.add_node("risk_assessor", risk_assessor.run)
    graph.add_node("decision_maker", decision_maker.run)
    graph.add_node("compliance_checker", compliance_checker.run)

    # 边：数据采集后分叉到两个分析 Agent
    graph.set_entry_point("data_collector")
    graph.add_edge("data_collector", "technical_analyst")
    graph.add_edge("data_collector", "fundamental_analyst")

    # 两个分析 Agent 都完成后汇合到风控
    graph.add_edge("technical_analyst", "risk_assessor")
    graph.add_edge("fundamental_analyst", "risk_assessor")

    # 风控 → 决策 → 合规 → 结束
    graph.add_edge("risk_assessor", "decision_maker")
    graph.add_edge("decision_maker", "compliance_checker")
    graph.add_edge("compliance_checker", END)

    return graph.compile()


# ---- 便捷入口 ----

async def run_advisory(query: str) -> dict:
    """运行一次完整的投顾分析链路。"""
    graph = build_graph()
    result = await graph.ainvoke({"query": query})
    return result


# ---- 测试入口 ----

if __name__ == "__main__":
    import asyncio

    async def main():
        query = "分析 600519 贵州茅台"
        print(f"查询: {query}")
        print("=" * 70)

        result = await run_advisory(query)

        if result.get("error"):
            print(f"错误: {result['error']}")
            return

        print("\n[技术面分析]")
        print(result.get("technical_report", "无")[:400])
        print("\n[基本面分析]")
        print(result.get("fundamental_report", "无")[:400])
        print("\n[风控评估]")
        print(result.get("risk_report", "无")[:400])
        print("\n[综合决策]")
        print(result.get("decision", "无")[:400])
        print("\n[合规审查]")
        print(result.get("compliance_result", "无"))
        print("\n[最终输出]")
        print(result.get("final_output", "无")[:400])

    asyncio.run(main())
