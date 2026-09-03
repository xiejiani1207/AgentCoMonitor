"""LangGraph 金融投顾 Agent 链路编排。

拓扑:
  数据采集 → 技术面分析 ∥ 基本面分析 → 风控评估
           → 价值投资 ∥ 趋势交易 ∥ 综合决策（三个候选决策）
           → END（筛选排序 + 合规审查由 orchestrator 后置完成）

用法:
  python demo_advisory/graph.py
  或
  from demo_advisory.graph import build_graph
"""

from typing import TypedDict

from langgraph.graph import END, StateGraph

from demo_advisory.agents import (
    data_collector,
    decision_maker,
    fundamental_analyst,
    risk_assessor,
    technical_analyst,
    trend_trader,
    value_investor,
)

# ---- State 定义 ----

class AdvisoryState(TypedDict, total=False):
    query: str                          # 用户查询
    demo_mode: bool                     # 演示模式（引导激进输出）
    stock_code: str | None              # 股票代码
    stock_name: str | None              # 股票名称
    collected_data: dict | None         # 数据采集结果
    technical_report: str               # 技术面分析报告
    fundamental_report: str             # 基本面分析报告
    risk_report: str                    # 风控评估报告
    decision: str                       # 综合决策（平衡）
    decision_value: str                 # 价值投资决策
    decision_trend: str                 # 趋势交易决策
    error: str | None                   # 错误信息


# ---- 构建 Graph ----

def build_graph() -> StateGraph:
    graph = StateGraph(AdvisoryState)

    # 注册所有节点
    graph.add_node("data_collector", data_collector.run)
    graph.add_node("technical_analyst", technical_analyst.run)
    graph.add_node("fundamental_analyst", fundamental_analyst.run)
    graph.add_node("risk_assessor", risk_assessor.run)
    graph.add_node("value_investor", value_investor.run)
    graph.add_node("trend_trader", trend_trader.run)
    graph.add_node("decision_maker", decision_maker.run)

    # 边：数据采集后分叉到两个分析 Agent
    graph.set_entry_point("data_collector")
    graph.add_edge("data_collector", "technical_analyst")
    graph.add_edge("data_collector", "fundamental_analyst")

    # 两个分析 Agent 都完成后汇合到风控
    graph.add_edge("technical_analyst", "risk_assessor")
    graph.add_edge("fundamental_analyst", "risk_assessor")

    # 风控后分叉到三个候选决策 Agent（并行），结束后汇合
    graph.add_edge("risk_assessor", "value_investor")
    graph.add_edge("risk_assessor", "trend_trader")
    graph.add_edge("risk_assessor", "decision_maker")
    graph.add_edge("value_investor", END)
    graph.add_edge("trend_trader", END)
    graph.add_edge("decision_maker", END)

    return graph.compile()


# ---- 测试入口 ----

if __name__ == "__main__":
    import asyncio

    async def main():
        query = "分析 600519 贵州茅台"
        graph = build_graph()
        result = await graph.ainvoke({"query": query})
        print(f"查询: {query}")
        print("=" * 70)
        print("[价值投资决策]")
        print(result.get("decision_value", "无")[:200])
        print("\n[趋势交易决策]")
        print(result.get("decision_trend", "无")[:200])
        print("\n[综合决策]")
        print(result.get("decision", "无")[:200])

    asyncio.run(main())
