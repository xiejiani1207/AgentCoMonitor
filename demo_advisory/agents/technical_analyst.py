"""Agent 2: 技术面分析 Agent。"""

from langchain_core.messages import HumanMessage, SystemMessage
from demo_advisory.agents._llm import get_llm, load_prompt

SYSTEM_PROMPT = load_prompt("technical_analyst.md")


def run(state: dict) -> dict:
    collected = state.get("collected_data")
    if not collected:
        return {**state, "technical_report": "错误: 无数据采集结果"}

    price = collected["price_snapshot"]
    daily = collected["daily_series"]
    name = collected["stock_name"]
    code = collected["stock_code"]

    daily_lines = ["日期      开盘    最高    最低    收盘    成交量"]
    for d in daily[-20:]:
        daily_lines.append(
            f"{d['date']}  {d['open']:>8}  {d['high']:>8}  {d['low']:>8}  {d['close']:>8}  {d['volume']:>10}")
    daily_text = "\n".join(daily_lines)

    indicator_text = (
        f"当前价: {price['current_price']}\n"
        f"MA5: {price['ma5']} | MA20: {price['ma20']} | MA60: {price['ma60']}\n"
        f"MACD: DIF={price['macd']['dif']}  DEA={price['macd']['dea']}  柱状线={price['macd']['histogram']}\n"
        f"RSI14: {price['rsi14']}\n"
        f"支撑位: {price['support']} | 压力位: {price['resistance']}\n"
        f"52周最低: {price['low_52w']} | 52周最高: {price['high_52w']}"
    )

    user_message = (
        f"请对以下 A 股进行技术面分析。\n\n"
        f"股票: {name} ({code})\n\n"
        f"=== 技术指标 ===\n{indicator_text}\n\n"
        f"=== 近 20 个交易日数据 ===\n{daily_text}"
    )

    try:
        llm = get_llm()
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ])
        report = response.content
    except Exception as e:
        report = f"技术面分析生成失败: {e}"

    return {"technical_report": report}
