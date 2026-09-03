"""合规判断——独立 LLM 语义合规审查（已从图节点改为后置函数）。

由 orchestrator（demo_service）在筛选出最优决策后调用，做语义合规兜底。
"""

import re

from langchain_core.messages import HumanMessage, SystemMessage

from demo_advisory.agents._llm import get_llm, load_prompt


def review_compliance(decision: str, name: str = "未知") -> dict:
    """审查一段投资决策，返回 {score, result}。"""
    if not decision:
        return {"score": 0, "result": "错误: 无决策内容"}

    try:
        llm = get_llm(temperature=0.0)  # 合规审查零温度，确保一致性
        system_prompt = load_prompt("compliance_checker.md")
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"请审查以下关于 {name} 的投资建议:\n\n{decision}"),
        ])
        result = response.content
    except Exception as e:
        result = f"合规审查失败: {e}"

    match = re.search(r"合规评分:\s*(\d+)", result)
    score = int(match.group(1)) if match else 0

    return {"score": score, "result": result}
