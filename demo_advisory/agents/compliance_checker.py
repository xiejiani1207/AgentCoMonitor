"""Agent 6: 合规判断 Agent。

这是 Demo 链路的最后一道闸门——审查综合决策的输出，判断能否对外发布。
"""

from langchain_core.messages import HumanMessage, SystemMessage

from demo_advisory.agents._llm import get_llm, load_prompt


def run(state: dict) -> dict:
    decision = state.get("decision", "")
    name = state.get("stock_name", "未知")

    if not decision:
        return {**state, "compliance_result": "错误: 无决策内容"}

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

    # 解析合规评分
    import re
    match = re.search(r"合规评分:\s*(\d+)", result)
    score = int(match.group(1)) if match else 0

    # 判断是否通过
    if score >= 70:
        final_output = f"[合规通过 评分:{score}]\n\n{decision}"
    elif score >= 40:
        final_output = f"[合规风险 评分:{score} 需修改]\n\n{decision}\n\n---\n合规审查意见:\n{result}"
    else:
        final_output = f"[合规拦截 评分:{score} 需人工审核]\n\n内容已被合规系统拦截，请人工审核后发布。"

    return {
        "compliance_result": result,
        "compliance_score": score,
        "final_output": final_output,
    }
