"""记忆 Agent——管理多轮对话上下文。

职责：根据对话历史解析当前用户提问，把省略指代（如「那」「它」「这个」）
补全为包含具体股票代码/名称的明确查询，供下游 Agent 使用。
"""

from langchain_core.messages import HumanMessage, SystemMessage

from demo_advisory.agents._llm import get_llm


def run(history: list[str], query: str) -> str:
    """解析当前查询，返回补全指代后的明确查询。

    Args:
        history: 之前各轮的用户提问（按时间顺序）
        query: 当前用户提问

    Returns:
        补全省略指代后的查询；无历史时原样返回。
    """
    if not history:
        return query

    history_text = "\n".join(f"- {h}" for h in history)
    prompt = (
        f"对话历史（按时间顺序）：\n{history_text}\n\n"
        f"当前用户提问：{query}\n\n"
        "请把提问中的省略指代（如「那」「它」「这个」）解析完整，"
        "输出一句明确、包含具体股票代码或名称的查询。只输出解析后的查询，不要任何解释。"
    )

    llm = get_llm(temperature=0.0)
    response = llm.invoke([
        SystemMessage(content="你是对话记忆 Agent，负责解析用户意图、补全省略指代。"),
        HumanMessage(content=prompt),
    ])
    return response.content.strip()
