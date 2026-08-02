"""Agent 1: 数据采集 Agent。

职责：解析用户查询 → 匹配目标股票 → 从 STOCK_DATA 提取完整数据包
输出：结构化的行情快照 + 日线摘要 + 财务概要，供下游分析 Agent 使用。

不调用 LLM——纯数据查询。这是整个 Demo 链路的唯一真实数据入口。
"""

from typing import Optional
from demo_advisory.mock_data.stocks import STOCK_DATA


def run(state: dict) -> dict:
    """
    从 State 中读取 query，查 STOCK_DATA，将结果写回 State。

    Args:
        state: LangGraph State，至少包含 {"query": str}

    Returns:
        更新后的 State，包含 collected_data
    """
    query = state.get("query", "").strip()

    # ---- 第 1 步：匹配股票 ----
    matched = _find_stock(query)

    if matched is None:
        return {
            "stock_code": None,
            "stock_name": None,
            "collected_data": None,
            "error": f"未找到匹配的股票，请检查代码或名称。已知股票: {_list_known()}",
        }

    code, stock = matched

    # ---- 第 2 步：提取数据包 ----
    price = stock["price"]
    daily = stock["daily"]
    fin = stock["financials"]

    # 行情快照
    price_text = (
        f"最新价: {price['current_price']} 元 | "
        f"MA5: {price['ma5']} | MA20: {price['ma20']} | MA60: {price['ma60']} | "
        f"RSI14: {price['rsi14']} | "
        f"支撑位: {price['support']} | 压力位: {price['resistance']} | "
        f"52周最低: {price['low_52w']} | 52周最高: {price['high_52w']}"
    )

    # 日线摘要（最近 5 天 + 关键统计）
    recent_5 = daily[-5:]
    daily_summary_lines = ["近 5 个交易日收盘价:"]
    for d in recent_5:
        daily_summary_lines.append(
            f"  {d['date']}: 开 {d['open']}  高 {d['high']}  低 {d['low']}  收 {d['close']}  量 {d['volume']}"
        )

    # 完整 60 日日线保留在 state 中供画图用
    daily_summary_text = "\n".join(daily_summary_lines)

    # 财务概要
    fin_lines = []
    if fin.get("pe_ttm"):
        fin_lines.append(f"滚动市盈率(PE TTM): {fin['pe_ttm']:.2f}")
    if fin.get("pb"):
        fin_lines.append(f"市净率(PB): {fin['pb']:.2f}")
    if fin.get("roe"):
        fin_lines.append(f"净资产收益率(ROE): {fin['roe']}%")
    if fin.get("revenue_growth"):
        fin_lines.append(f"营收增长率: {fin['revenue_growth']}%")
    if fin.get("profit_growth"):
        fin_lines.append(f"利润增长率: {fin['profit_growth']}%")
    fin_text = " | ".join(fin_lines) if fin_lines else "财务数据暂无"

    # ---- 第 3 步：组装输出 ----
    collected_data = {
        "stock_code": code,
        "stock_name": stock["name"],
        "industry": stock["industry"],
        "price_snapshot": price,       # 技术指标快照
        "daily_series": daily,         # 60 天日线（原始数据）
        "financials": fin,             # 财务原始数据
        # 供下游 Agent 直接使用的人类可读摘要
        "summary": (
            f"股票: {stock['name']} ({code}) | 行业: {stock['industry']}\n"
            f"行情: {price_text}\n"
            f"财务: {fin_text}\n"
            f"{daily_summary_text}"
        ),
    }

    return {
        "stock_code": code,
        "stock_name": stock["name"],
        "collected_data": collected_data,
    }


# ---- 内部匹配逻辑 ----

def _find_stock(query: str) -> Optional[tuple[str, dict]]:
    """在 STOCK_DATA 中按代码或名称匹配股票。"""
    # 直接代码匹配（如 "600519"）
    if query in STOCK_DATA:
        return query, STOCK_DATA[query]

    # 按名称模糊匹配
    query_lower = query.lower()
    for code, stock in STOCK_DATA.items():
        if stock["name"] in query or query_lower in stock["name"].lower():
            return code, stock

    # 从文本中提取 6 位数字代码
    import re
    matches = re.findall(r"\b(\d{6})\b", query)
    for m in matches:
        if m in STOCK_DATA:
            return m, STOCK_DATA[m]

    return None


def _list_known() -> str:
    return ", ".join(f"{c}({s['name']})" for c, s in STOCK_DATA.items())
