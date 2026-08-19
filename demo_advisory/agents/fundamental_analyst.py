"""Agent 3: 基本面分析 Agent。"""

from langchain_core.messages import HumanMessage, SystemMessage

from demo_advisory.agents._llm import get_llm, load_prompt


def run(state: dict) -> dict:
    collected = state.get("collected_data")
    if not collected:
        return {**state, "fundamental_report": "错误: 无数据采集结果"}

    fin = collected["financials"]
    name = collected["stock_name"]
    code = collected["stock_code"]

    fin_text = (
        f"滚动市盈率(PE TTM): {fin.get('pe_ttm', 'N/A')}\n"
        f"市净率(PB): {fin.get('pb', 'N/A')}\n"
        f"净资产收益率(ROE): {fin.get('roe', 'N/A')}%\n"
        f"营收增长率: {fin.get('revenue_growth', 'N/A')}%\n"
        f"利润增长率: {fin.get('profit_growth', 'N/A')}%\n"
    )

    try:
        llm = get_llm()
        system_prompt = load_prompt("fundamental_analyst.md")
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"股票: {name} ({code})\n\n{fin_text}"),
        ])
        report = response.content
    except Exception as e:
        report = f"基本面分析生成失败: {e}"

    return {"fundamental_report": report}
