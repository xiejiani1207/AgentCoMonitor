"""Agent 5: 综合决策 Agent。"""

from langchain_core.messages import HumanMessage, SystemMessage

from demo_advisory.agents._llm import get_llm, load_prompt

SYSTEM_PROMPT = load_prompt("decision_maker.md")


def run(state: dict) -> dict:
    tech = state.get("technical_report", "")
    fund = state.get("fundamental_report", "")
    risk = state.get("risk_report", "")
    name = state.get("stock_name", "未知")

    if not tech or not fund or not risk:
        return {**state, "decision": "错误: 缺少分析报告"}

    # 组装上下文
    context = (
        f"股票: {name}\n\n"
        f"=== 技术面分析 ===\n{tech}\n\n"
        f"=== 基本面分析 ===\n{fund}\n\n"
        f"=== 风控评估 ===\n{risk}"
    )

    try:
        llm = get_llm(temperature=0.2)
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=context),
        ])
        decision = response.content
    except Exception as e:
        decision = f"综合决策生成失败: {e}"

    return {"decision": decision}
