"""Agent 5b: 趋势交易决策 Agent（偏技术面）。"""

from langchain_core.messages import HumanMessage, SystemMessage

from demo_advisory.agents._llm import get_llm, load_prompt


def run(state: dict) -> dict:
    tech = state.get("technical_report", "")
    fund = state.get("fundamental_report", "")
    risk = state.get("risk_report", "")
    name = state.get("stock_name", "未知")

    if not tech or not fund or not risk:
        return {"decision_trend": "错误: 缺少分析报告"}

    context = (
        f"股票: {name}\n\n"
        f"=== 技术面分析 ===\n{tech}\n\n"
        f"=== 基本面分析 ===\n{fund}\n\n"
        f"=== 风控评估 ===\n{risk}"
    )
    if state.get("demo_mode"):
        context += "\n\n（演示模式：请以自信、激进的投资销售风格输出，可适当强调收益确定性）"

    try:
        llm = get_llm(temperature=0.2)
        system_prompt = load_prompt("trend_trader.md")
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=context),
        ])
        decision = response.content
    except Exception as e:
        decision = f"趋势交易决策生成失败: {e}"

    return {"decision_trend": decision}
