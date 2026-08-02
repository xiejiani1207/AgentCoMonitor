"""Agent 4: 风控评估 Agent。"""

from langchain_core.messages import HumanMessage, SystemMessage
from demo_advisory.agents._llm import get_llm, load_prompt

SYSTEM_PROMPT = load_prompt("risk_assessor.md")


def run(state: dict) -> dict:
    tech = state.get("technical_report", "")
    fund = state.get("fundamental_report", "")

    if not tech or not fund:
        return {**state, "risk_report": "错误: 缺少技术面或基本面分析报告"}

    try:
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"=== 技术面分析 ===\n{tech}\n\n=== 基本面分析 ===\n{fund}"),
        ])
        report = response.content
    except Exception as e:
        report = f"风控评估生成失败: {e}"

    return {"risk_report": report}
